import grpc
import logging
import zab_peer_pb2
import zab_client_pb2
import zab_peer_pb2_grpc
import zab_client_pb2_grpc
from google.protobuf.empty_pb2 import Empty

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s:%(lineno)s %(levelname)s [%(threadName)s] %(message)s")
logger = logging.getLogger(__name__)

class ZabClientService(zab_client_pb2_grpc.ZabClientServiceServicer):
    def __init__(self, wrapper):
        logger.info(f"Init ZabClientService")
        self.wrapper = wrapper

    def ReadAccount(self, request, context):
        logger.info(f"Received election notification")
        logger.info(f"{request, context}")
        return zab_client_pb2.ReadAccountResponse(balance=self.wrapper.balance)

    def WriteTransaction(self, request, context):
        return Empty()
    
    def DebugReadAccount(self, request, context):
        return Empty()
    
    def DebugWriteTransaction(self, request, context):
        return Empty()
