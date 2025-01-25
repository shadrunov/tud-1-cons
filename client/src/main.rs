use crate::zab::BankTransaction;
use crate::zab_client::zab_client_service_client::ZabClientServiceClient;
use crate::zab_client::{ReadAccountRequest, WriteTransactionRequest};
use chrono::Utc;
use clap::Parser;
use csv::Writer;
use futures::stream::FuturesUnordered;
use futures::stream::StreamExt;
use serde::Serialize;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use tokio::time::interval;
use tonic::transport::Channel;
use tonic::Request;

pub mod zab {
    tonic::include_proto!("zab");
}

pub mod zab_client {
    tonic::include_proto!("zab_client");
}

pub type PeerId = u32;

pub type ZabClient = ZabClientServiceClient<Channel>;

#[derive(Parser, Debug)]
struct Cli {
    #[clap(short, long, value_delimiter = ',', num_args = 1..)]
    peers: Vec<String>,

    #[clap(short, long, default_value_t = 10)]
    runtime: u64,

    #[clap(short, long, default_value_t = 16)]
    num_threads: usize,

    #[clap(short, long, default_value_t = false)]
    check_also_follower_balances: bool,
}

#[derive(Debug, Serialize)]
pub struct BenchmarkRow {
    pub time: String,
    pub rate: usize,
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    let num_curr_sec_tuples_sent = Arc::new(AtomicUsize::new(0));
    let log_interval = interval(Duration::from_secs(1));
    create_log_thread(log_interval, num_curr_sec_tuples_sent.clone());

    let mut peers = connect_to_peers(cli.peers).await;

    let mut clients = vec![];
    let is_running = Arc::new(AtomicBool::new(true));

    let original_balances = get_previous_balances(&mut peers, cli.num_threads).await;

    let expected_balances = Arc::new((0..cli.num_threads).map(|i| Mutex::new(original_balances[i])).collect::<Vec<_>>());
    for thread_id in 0..cli.num_threads {
        clients.push(tokio::task::spawn(create_benchmark_client(thread_id, peers.clone(), num_curr_sec_tuples_sent.clone(), is_running.clone(), expected_balances.clone())));
    }

    tokio::time::sleep(Duration::from_secs(cli.runtime)).await;
    is_running.store(false, Ordering::Relaxed);

    for client in clients {
        client.await.unwrap();
    }

    wait_for_no_more_outstanding_transactions(&mut peers).await;

    check_if_balances_match(&mut peers, expected_balances, cli.check_also_follower_balances).await;
}

async fn get_previous_balances(peers: &mut [ZabClient], num_threads: usize) -> Vec<i32> {
    let mut original_balances = vec![0; num_threads];
    for (i, original_balance) in original_balances.iter_mut().enumerate() {
        for peer in peers.iter_mut() {
            match peer.read_account(ReadAccountRequest {
                account_id: i.try_into().unwrap(),
            }).await {
                Ok(balance) => {
                    *original_balance = balance.into_inner().balance;
                    break;
                }
                Err(_) => continue,
            }
        }
    }
    original_balances
}

async fn wait_for_no_more_outstanding_transactions(peers: &mut [ZabClient]) {
    loop {
        let mut futures = peers.iter_mut().map(|client| {
            async move {
                client.debug_has_outstanding_transactions(Request::new(())).await
            }
        }).collect::<FuturesUnordered<_>>();
        let mut all_done = true;
        while let Some(result) = futures.next().await {
            if let Ok(result) = result {
                if result.into_inner().has_outstanding_transactions {
                    all_done = false;
                    break;
                }
            }
        }
        if all_done {
            break;
        }
    }
}

async fn check_if_balances_match(peers: &mut [ZabClient], expected_balances: Arc<Vec<Mutex<i32>>>, check_also_follower_balances: bool) {
    for (i, expected_balance) in expected_balances.iter().enumerate() {
        let mut futures = peers.iter_mut().map(|client| {
            async move {
                if check_also_follower_balances {
                    client.debug_read_account(Request::new(ReadAccountRequest {
                        account_id: i.try_into().unwrap(),
                    })).await
                } else {
                    client.read_account(Request::new(ReadAccountRequest {
                        account_id: i.try_into().unwrap(),
                    })).await
                }
            }
        }).collect::<FuturesUnordered<_>>();
        while let Some(result) = futures.next().await {
            if let Ok(result) = result {
                let balance = result.into_inner().balance;
                let expected_balance = *expected_balance.lock().await;
                if balance != expected_balance {
                    println!("Error | Mismatched balance for account {}. Was: {} | Expected: {}", i, balance, expected_balance);
                } else {
                    println!("Balance for account {} matches expected: {}", i, balance);
                }
            }
        }
    }
}

async fn create_benchmark_client(thread_id: usize, mut peers: Vec<ZabClient>, num_curr_sec_tuples_sent: Arc<AtomicUsize>, is_running: Arc<AtomicBool>, expected_balances: Arc<Vec<Mutex<i32>>>) {
    let mut inc_amount = 0;
    println!("Thread {} started", thread_id);
    while is_running.load(Ordering::Relaxed) {
        for client in peers.iter_mut() {
            let request = Request::new(WriteTransactionRequest {
                transaction: Some(BankTransaction {
                    account_id: thread_id as u32,
                    amount: inc_amount,
                }),
            });

            if client.write_transaction(request).await.is_ok() {
                num_curr_sec_tuples_sent.fetch_add(1, Ordering::Relaxed);
                *expected_balances[thread_id].lock().await += inc_amount;
                inc_amount += 1;
                break;
            }
        }
    }
}

fn create_log_thread(
    mut log_interval: tokio::time::Interval,
    num_curr_sec_tuples_sent: Arc<AtomicUsize>,
) -> tokio::task::JoinHandle<()> {
    let mut log_writer = Writer::from_path("logs/log.csv").unwrap();
    tokio::spawn(async move {
        let mut already_started = false;
        loop {
            log_interval.tick().await;

            let rate = num_curr_sec_tuples_sent.swap(0, Ordering::AcqRel);

            println!("Number of tuples sent: {}", rate);

            if !already_started {
                if rate == 0 {
                    continue;
                }
                already_started = true;
            }

            log_writer.serialize(
                BenchmarkRow {
                    time: Utc::now().to_rfc3339(),
                    rate,
                }
            ).unwrap();
            log_writer.flush().unwrap();
        }
    })
}

async fn connect_to_peers(cli_clients: Vec<String>) -> Vec<ZabClient> {
    let mut peers = Vec::with_capacity(cli_clients.len());

    for addr in cli_clients {
        peers.push(try_connect_to_peer(addr).await);
    }

    println!("Connected to all peers!");

    peers
}

async fn try_connect_to_peer(addr: String) -> ZabClient {
    loop {
        match ZabClientServiceClient::connect(format!("https://{}", addr)).await {
            Ok(client) => return client,
            Err(e) => {
                println!("Failed to connect to peer: {}. Retrying...", e);
                tokio::time::sleep(Duration::from_secs(5)).await;
            }
        }
    }
}