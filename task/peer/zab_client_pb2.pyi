import types_pb2 as _types_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class WriteTransactionRequest(_message.Message):
    __slots__ = ("transaction",)
    TRANSACTION_FIELD_NUMBER: _ClassVar[int]
    transaction: _types_pb2.BankTransaction
    def __init__(self, transaction: _Optional[_Union[_types_pb2.BankTransaction, _Mapping]] = ...) -> None: ...

class ReadAccountRequest(_message.Message):
    __slots__ = ("account_id",)
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    account_id: int
    def __init__(self, account_id: _Optional[int] = ...) -> None: ...

class ReadAccountResponse(_message.Message):
    __slots__ = ("balance",)
    BALANCE_FIELD_NUMBER: _ClassVar[int]
    balance: int
    def __init__(self, balance: _Optional[int] = ...) -> None: ...

class DebugHasOutstandingTransactionsResponse(_message.Message):
    __slots__ = ("has_outstanding_transactions",)
    HAS_OUTSTANDING_TRANSACTIONS_FIELD_NUMBER: _ClassVar[int]
    has_outstanding_transactions: bool
    def __init__(self, has_outstanding_transactions: bool = ...) -> None: ...
