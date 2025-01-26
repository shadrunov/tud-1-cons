import grpc
import logging
import zab_peer_pb2
import zab_client_pb2
import zab_peer_pb2_grpc
import zab_client_pb2_grpc
from google.protobuf.empty_pb2 import Empty

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s:%(lineno)s %(levelname)s [%(threadName)s] %(message)s")
logger = logging.getLogger(__name__)


class ZabPeerService(zab_peer_pb2_grpc.ZabPeerServiceServicer):
    def __init__(self, wrapper):
        logger.info(f"Init ZabPeerService")
        self.wrapper = wrapper

    def SendHeartbeat(self, request, context):
        logger.info(f"Received heartbeat")
        return Empty()

    def SendElectionNotification(self, request, context):
        logger.info(f"Received election notification from {context.peer()} \n{request}")
        return Empty()