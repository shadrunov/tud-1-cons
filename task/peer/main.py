from concurrent import futures
import logging
import time
import threading
import operator
from collections import defaultdict

import grpc
import zab_peer_pb2
import zab_client_pb2
import zab_peer_pb2_grpc
import zab_client_pb2_grpc
import argparse
from google.protobuf.empty_pb2 import Empty
import types_pb2 as tp

from client_service import ZabClientService
from peer_service import ZabPeerService
from google.protobuf.json_format import MessageToDict


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

        logger.info(f"Done elections. Current state: {self.master.shared_map['state']}")

        while self.running:
            time.sleep(0.5)
            logger.info(f"Sending election notification")
            # self.send_election_notification()

    @staticmethod
    def make_election_request(shared_map):
        election_request = zab_peer_pb2.ElectionRequest(
            vote=shared_map["vote"],
            id=shared_map["id"],
            state=shared_map["state"],
            round=shared_map["round"],
        )
        logger.debug(f"Made election request: {MessageToDict(election_request)}")
        return election_request

    @staticmethod
    def send_election_request(url, election_request):
        logger.debug(f"Sending election request: {MessageToDict(election_request)}")
        with grpc.insecure_channel(url) as channel:
            stub = zab_peer_pb2_grpc.ZabPeerServiceStub(channel)
            response = stub.SendElectionNotification(election_request)
            logger.info(f"Received response from {url}: {response}")

    def send_election_request_to_all(self, election_request):
        for peer in self.master.members:  # include self
            logger.info(f"Sending election request to peer {peer}")
            url = self.master.get_url(peer)
            self.send_election_request(url, election_request)

    @staticmethod
    def is_le_zxid(zxid1, zxid2):
        if zxid1.epoch < zxid2.epoch or (
            zxid1.epoch == zxid2.epoch and zxid1.counter < zxid2.counter
        ):
            return True
        return False

    @staticmethod
    def is_geq_zxid(zxid1, zxid2):
        return not Worker.is_le_zxid(zxid1, zxid2)

    @staticmethod
    def is_ge_zxid(zxid1, zxid2):
        if zxid1.epoch > zxid2.epoch or (
            zxid1.epoch == zxid2.epoch and zxid1.counter > zxid2.counter
        ):
            return True
        return False

    @staticmethod
    def is_geq_vote(vote1, vote2):
        if Worker.is_ge_zxid(vote1.last_zx_id, vote2.last_zx_id) or (
            vote1.last_zx_id == vote2.last_zx_id and vote1.id >= vote2.id
        ):
            return True
        return False

    @staticmethod
    def is_ge_vote(vote1, vote2):
        if Worker.is_ge_zxid(vote1.last_zx_id, vote2.last_zx_id) or (
            vote1.last_zx_id == vote2.last_zx_id and vote1.id > vote2.id
        ):
            return True
        return False

    @staticmethod
    def is_le_vote(vote1, vote2):
        return not Worker.is_geq_vote(vote1, vote2)

    @staticmethod
    def put(shared_map, table_name, key, value):
        """put to table"""
        table = shared_map[table_name]
        if key in table:
            version = table[key][-1]  # get version
            value.append(version + 1)
            logger.debug(
                f"Key {key} was in table. Version: {version}, new value: {value}"
            )
        else:
            value.append(1)
            logger.debug(
                f"Key {key} was not in table. Version: {1}, new value: {value}"
            )
        table[key] = value
        logger.debug(f"Put to {table_name}: {key, value}")

    def get_quorum_vote(self, table_name="ReceivedVotes"):
        quorum = (len(self.master.peers) // 2) + 1
        if len(self.master.shared_map[table_name]) < quorum:
            return None

        tally = defaultdict(int)
        logger.debug(f"ReceivedVotes: {self.master.shared_map[table_name]}")
        for vote in self.master.shared_map[table_name].values():
            vote_id = vote[0].id
            tally[vote_id] += 1

        results = sorted(tally.items(), key=operator.itemgetter(1), reverse=True)
        leader_id, leader_count = results[0]
        # is there a tie?
        if list(tally.values()).count(leader_count) > 1:
            return None
        return leader_id

    def do_elections(self):
        logger.info(f"Starting elections")
        timeout = 0.25
        with self.master.shared_map_lock:
            self.master.shared_map["queue"] = []
            self.master.shared_map["ReceivedVotes"] = {}
            self.master.shared_map["OutOfElection"] = {}
            self.master.shared_map["state"] = tp.State.Election
            self.master.shared_map["id"] = self.master.id
            self.master.shared_map["lastZxid"] = tp.ZxId(epoch=0, counter=0)
            self.master.shared_map["round"] = 1
            self.master.shared_map["vote"] = tp.Vote(
                id=self.master.id, last_zx_id=tp.ZxId(epoch=0, counter=0)
            )

        # election_request = self.make_election_request(self.master.shared_map)
        # self.send_election_request_to_all(election_request)

        while self.master.shared_map["state"] == tp.State.Election:
            logger.info(f"Popping queue")
            n = (
                self.master.shared_map["queue"].pop(0)
                if self.master.shared_map["queue"]
                else None
            )
            if n is None:
                logger.info(f"Queue is empty, sending election request to all")
                timeout *= 2 if timeout < 5 else 5
                election_request = self.make_election_request(self.master.shared_map)
                self.send_election_request_to_all(election_request)
            elif n.state == tp.State.Election:
                logger.info(f"Queue is not empty. Processing 1 {MessageToDict(n)}")
                if n.round > self.master.shared_map["round"]:
                    logger.info(
                        f"188 n.round > self.master.shared_map['round']. setting received votes to empty"
                    )
                    with self.master.shared_map_lock:
                        self.master.shared_map["round"] = n.round
                        self.master.shared_map["ReceivedVotes"] = {}
                        # if n.vote > (P.lastZxid, P.id)
                        if self.is_ge_vote(
                            n.vote,
                            tp.Vote(
                                self.master.shared_map["id"],
                                self.master.shared_map["lastZxid"],
                            ),
                        ):
                            self.master.shared_map["vote"] = n.vote
                        else:
                            self.master.shared_map["vote"] = tp.Vote(
                                self.master.shared_map["id"],
                                self.master.shared_map["lastZxid"],
                            )

                    election_request = self.make_election_request(
                        self.master.shared_map
                    )
                    self.send_election_request_to_all(election_request)

                elif n.round == self.master.shared_map["round"] and self.is_ge_vote(
                    n.vote, self.master.shared_map["vote"]
                ):
                    logger.info(
                        f"214 n.round == self.master.shared_map['round'] and n.vote > self.master.shared_map['vote']. accepting the vote"
                    )
                    with self.master.shared_map_lock:
                        self.master.shared_map["vote"] = n.vote
                    logger.info(
                        f"New our vote: {MessageToDict(self.master.shared_map['vote'])}"
                    )

                    election_request = self.make_election_request(
                        self.master.shared_map
                    )
                    self.send_election_request_to_all(election_request)
                    logger.info(f"Sent our new vote to all")

                elif n.round < self.master.shared_map["round"]:
                    logger.info("n.round < shared_map.round. going to next round")
                    continue
                with self.master.shared_map_lock:
                    logger.debug(f"Putting to ReceivedVotes: {n.id, [n.vote, n.round]}")
                    self.put(
                        self.master.shared_map, "ReceivedVotes", n.id, [n.vote, n.round]
                    )

                if len(self.master.shared_map["ReceivedVotes"]) == len(
                    self.master.members
                ):
                    with self.master.shared_map_lock:
                        if self.master.shared_map["vote"].id == self.master.id:
                            self.master.shared_map["state"] = tp.State.Leading
                        else:
                            self.master.shared_map["state"] = tp.State.Following
                    logger.info(
                        f"Peer {self.master.id} is {self.master.shared_map['state']}"
                    )
                    return self.master.shared_map["vote"]

                # if P.vote has a quorum in ReceivedVotes
                with self.master.shared_map_lock:
                    if self.get_quorum_vote() == self.master.shared_map["vote"].id:
                        if self.master.shared_map["vote"].id == self.master.id:
                            self.master.shared_map["state"] = tp.State.Leading
                        else:
                            self.master.shared_map["state"] = tp.State.Following
                        logger.info(
                            f"Peer {self.master.id} is {self.master.shared_map['state']}"
                        )
                        return self.master.shared_map["vote"]
            else:  # state of n is LEADING or FOLLOWING
                logger.info(f"Queue is not empty. Processing 2 {MessageToDict(n)}")
                if n.round == self.master.shared_map["round"]:
                    with self.master.shared_map_lock:
                        self.put(
                            self.master.shared_map,
                            "ReceivedVotes",
                            n.id,
                            [n.vote, n.round],
                        )
                    if n.state == tp.State.Leading:
                        with self.master.shared_map_lock:
                            if n.vote.id == self.master.id:
                                self.master.shared_map["state"] = tp.State.Leading
                            else:
                                self.master.shared_map["state"] = tp.State.Following
                            return n.vote
                    elif (
                        n.vote.id == self.master.id
                        and self.get_quorum_vote() == n.vote.id
                    ):
                        with self.master.shared_map_lock:
                            if n.vote.id == self.master.id:
                                self.master.shared_map["state"] = tp.State.Leading
                            else:
                                self.master.shared_map["state"] = tp.State.Following
                            return n.vote
                    elif (
                        self.get_quorum_vote() == n.vote.id
                        and self.get_state(n.id).state == tp.State.Leading
                        and n.vote.id in self.master.shared_map["OutOfElection"]
                    ):
                        with self.master.shared_map_lock:
                            if n.vote.id == self.master.id:
                                self.master.shared_map["state"] = tp.State.Leading
                            else:
                                self.master.shared_map["state"] = tp.State.Following
                            return n.vote
                with self.master.shared_map_lock:
                    self.put(
                        self.master.shared_map, "OutOfElection", n.id, [n.vote, n.round]
                    )
                if (
                    n.vote.id == self.master.id
                    and self.get_quorum_vote(table_name="OutOfElection") == n.vote.id
                ):
                    with self.master.shared_map_lock:
                        self.shared_map["round"] = n.round
                        if n.vote.id == self.master.id:
                            self.master.shared_map["state"] = tp.State.Leading
                        else:
                            self.master.shared_map["state"] = tp.State.Following
                        return n.vote
                elif (
                    self.get_quorum_vote(table_name="OutOfElection") == n.vote.id
                    and self.get_state(n.vote.id).state == tp.State.Leading
                    and n.vote.id in self.master.shared_map["OutOfElection"]
                ):
                    with self.master.shared_map_lock:
                        self.shared_map["round"] = n.round
                        if n.vote.id == self.master.id:
                            self.master.shared_map["state"] = tp.State.Leading
                        else:
                            self.master.shared_map["state"] = tp.State.Following
                        return n.vote
            logger.info(f"Sleeping: {timeout}")
            time.sleep(timeout)

    def get_state(self, peer_id):
        url = self.master.get_url(peer_id)
        with grpc.insecure_channel(url) as channel:
            stub = zab_peer_pb2_grpc.ZabPeerServiceStub(channel)
            response = stub.GetState(Empty())
            logger.info(f"Received response from {url}: {response}")
            return response

    def do_recovery(self):
        if self.master.shared_map["state"] == tp.State.Leading:
            self.do_recovery_leading()
        elif self.master.shared_map["state"] == tp.State.Following:
            self.do_recovery_following()

    def do_recovery_leading(self):
        with self.master.shared_map_lock:
            self.master.shared_map["lastZxid"] = tp.ZxId(
                epoch=self.master.shared_map["lastZxid"].epoch + 1, counter=0
            )


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
        self.peers = {}
        for peer in args.peers.split(","):
            peer_id, peer_host, peer_port = peer.split(":")
            self.peers[int(peer_id)] = (peer_host, int(peer_port))
        self.members = {self.id: (self.host, self.port)} | self.peers

        self.shared_map = {}
        self.shared_map_lock = threading.Lock()
        logger.info(
            f"Initiated peer {self.id} on port {self.port}. Peers: {self.peers}"
        )
        logger.info(f"Members: {self.members}")

    def get_url(self, peer_id):
        return f"{self.members[peer_id][0]}:{self.members[peer_id][1]}"

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
