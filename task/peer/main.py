from concurrent import futures
import logging
import time
import threading

import grpc
import zab_peer_pb2
import zab_client_pb2
import zab_peer_pb2_grpc
import zab_client_pb2_grpc
import argparse
import types_pb2 as tp

from client_service import ZabClientService
from peer_service import ZabPeerService

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s:%(lineno)s %(levelname)s [%(threadName)s] %(message)s",
)
logger = logging.getLogger(__name__)


class ServerWrapper:
    def __init__(self, master):
        logger.info(f"Init server on port {master.port}")
        self.master = master
        self.port = master.port
        self.balance = 55
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
        zab_peer_pb2_grpc.add_ZabPeerServiceServicer_to_server(
            ZabPeerService(self), self.server
        )
        zab_client_pb2_grpc.add_ZabClientServiceServicer_to_server(
            ZabClientService(self), self.server
        )
        self.server.add_insecure_port(f"[::]:{self.port}")

    def start(self):
        logger.info(f"Starting server on port {self.port}")
        self.server.start()
        logger.info(f"Server started, listening on {self.port}")

    def wait_for_termination(self):
        self.server.wait_for_termination()


class Worker(threading.Thread):
    def __init__(self, master):
        logger.info(f"Init worker")
        super(Worker, self).__init__()
        self.daemon = True
        self.running = False
        self.master = master

        # self.channel = grpc.insecure_channel(host + ":" + port)
        # self.stub = zab_peer_pb2_grpc.ZabPeerServiceStub(self.channel)
        logger.info(f"Initiated worker")

    def run(self):
        self.running = True

        self.do_elections()

        while self.running:
            time.sleep(0.5)
            logger.info(f"Sending election notification")
            # self.send_election_notification()

    def do_elections(self):
        logger.info(f"Starting elections")
        with self.master.shared_map_lock:
            self.master.shared_map["state"] = tp.State.Election
            self.master.shared_map["id"] = self.master.id
            self.master.shared_map["lastZxid"] = tp.ZxId(epoch=0, counter=0)
            self.master.shared_map["round"] = 1

        vote = tp.Vote(
            id=self.master.shared_map["id"], last_zx_id=self.master.shared_map["lastZxid"]
        )
        state = tp.State.Election
        election_request = zab_peer_pb2.ElectionRequest(
            vote=vote,
            id=self.master.shared_map["id"],
            state=state,
            round=self.master.shared_map["round"],
        )
        for peer in [(self.master.id, self.master.host, self.master.port)] + self.master.peers:  # include self
            logger.info(f"Sending election notification to {peer}")
            with grpc.insecure_channel(f"{peer[1]}:{peer[2]}") as channel:
                stub = zab_peer_pb2_grpc.ZabPeerServiceStub(channel)
                response = stub.SendElectionNotification(election_request)
                logger.info(f"Received response from {peer[1]}: {response}")

        logger.info(f"Done elections")

    def send_election_notification(self, request):
        return self.stub.SendElectionNotification(request)


class MyPeer:
    def parse_args(self):
        parser = argparse.ArgumentParser(description="Start a Zab peer.")
        parser.add_argument("--id", type=int, required=True, help="ID of the peer")
        parser.add_argument(
            "--port", type=int, required=True, help="Port number of the peer"
        )
        parser.add_argument(
            "--peers",
            type=str,
            required=True,
            help="Comma-separated list of peers in the format id:host:port",
        )
        return parser.parse_args()

    def __init__(self):
        args = self.parse_args()
        self.id = args.id
        self.port = args.port
        self.host = "localhost"
        self.peers = []
        for peer in args.peers.split(","):
            peer_id, peer_host, peer_port = peer.split(":")
            self.peers.append((int(peer_id), peer_host, int(peer_port)))

        self.shared_map = {}
        self.shared_map_lock = threading.Lock()
        logger.info(
            f"Initiated peer {self.id} on port {self.port}. Peers: {self.peers}"
        )

    def run(self):
        self.running = True
        self.server_wrapper = ServerWrapper(self)
        self.worker = Worker(self)

        logger.info(f"Starting server and client")
        self.server_wrapper.start()
        self.worker.start()

        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping...")
            self.running = False
            self.worker.running = False
            self.server_wrapper.server.stop(0)
            logger.info("Stopped server")


if __name__ == "__main__":
    peer = MyPeer()
    peer.run()
