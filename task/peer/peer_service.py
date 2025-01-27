import grpc
import logging
import zab_peer_pb2
import zab_client_pb2
import zab_peer_pb2_grpc
import zab_client_pb2_grpc
from google.protobuf.empty_pb2 import Empty
import types_pb2 as tp
from google.protobuf.json_format import MessageToDict

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s:%(lineno)s %(levelname)s [%(threadName)s] %(message)s",
)
logger = logging.getLogger(__name__)


class ZabPeerService(zab_peer_pb2_grpc.ZabPeerServiceServicer):
    def __init__(self, wrapper):
        logger.info(f"Init ZabPeerService")
        self.wrapper = wrapper

    def SendHeartbeat(self, request, context):
        logger.info(f"Received heartbeat")
        return Empty()

    def SendElectionNotification(self, request, context):
        logger.info(f"Received election notification {MessageToDict(request)}")
        logger.info(
            f"Peer vote: id {request.vote.id} last_zx_id epoch {request.vote.last_zx_id.epoch} counter {request.vote.last_zx_id.counter}"
        )
        logger.info(
            f"Peer id: {request.id}, Peer state: {request.state} {tp.State.Name(request.state)}, Peer round: {request.round}"
        )

        with self.wrapper.master.shared_map_lock:
            shared_map = self.wrapper.master.shared_map
            if shared_map["state"] == tp.State.Election:
                logger.info(f"Appending request to queue")
                shared_map["queue"].append(request)
                if (
                    request.state == tp.State.Election
                    and request.round < shared_map["round"]
                ):
                    logger.info(f"Peer {request.id} has lower round")
                    req = self.wrapper.master.worker.make_election_request(shared_map)
                    url = self.wrapper.master.get_url(request.id)
                    self.wrapper.master.worker.send_election_request(url, req)
                return Empty()
            elif request.state == tp.State.Election:
                logger.info(f"Peer {request.id} in election, sending notification")
                req = self.wrapper.master.worker.make_election_request(shared_map)
                url = self.wrapper.master.get_url(request.id)
                self.wrapper.master.worker.send_election_request(url, req)
        return Empty()

    def GetState(self, request, context):
        logger.info(f"Received GetState request")
        shared_map = self.wrapper.master.shared_map
        return zab_peer_pb2.GetStateResponse(state=shared_map["state"])
