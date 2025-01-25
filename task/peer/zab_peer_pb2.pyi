from google.protobuf import empty_pb2 as _empty_pb2
import types_pb2 as _types_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ElectionRequest(_message.Message):
    __slots__ = ("vote", "id", "state", "round")
    VOTE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ROUND_FIELD_NUMBER: _ClassVar[int]
    vote: _types_pb2.Vote
    id: int
    state: _types_pb2.State
    round: int
    def __init__(self, vote: _Optional[_Union[_types_pb2.Vote, _Mapping]] = ..., id: _Optional[int] = ..., state: _Optional[_Union[_types_pb2.State, str]] = ..., round: _Optional[int] = ...) -> None: ...

class GetStateResponse(_message.Message):
    __slots__ = ("state",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    state: _types_pb2.State
    def __init__(self, state: _Optional[_Union[_types_pb2.State, str]] = ...) -> None: ...

class FollowerInfoRequest(_message.Message):
    __slots__ = ("last_zx_id",)
    LAST_ZX_ID_FIELD_NUMBER: _ClassVar[int]
    last_zx_id: _types_pb2.ZxId
    def __init__(self, last_zx_id: _Optional[_Union[_types_pb2.ZxId, _Mapping]] = ...) -> None: ...

class FollowerInfoResponse(_message.Message):
    __slots__ = ("last_zx_id", "trunc", "diff", "snap")
    LAST_ZX_ID_FIELD_NUMBER: _ClassVar[int]
    TRUNC_FIELD_NUMBER: _ClassVar[int]
    DIFF_FIELD_NUMBER: _ClassVar[int]
    SNAP_FIELD_NUMBER: _ClassVar[int]
    last_zx_id: _types_pb2.ZxId
    trunc: _types_pb2.Trunc
    diff: _types_pb2.Diff
    snap: _types_pb2.Snap
    def __init__(self, last_zx_id: _Optional[_Union[_types_pb2.ZxId, _Mapping]] = ..., trunc: _Optional[_Union[_types_pb2.Trunc, _Mapping]] = ..., diff: _Optional[_Union[_types_pb2.Diff, _Mapping]] = ..., snap: _Optional[_Union[_types_pb2.Snap, _Mapping]] = ...) -> None: ...

class ProposeTransactionRequest(_message.Message):
    __slots__ = ("zx_id", "transaction")
    ZX_ID_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_FIELD_NUMBER: _ClassVar[int]
    zx_id: _types_pb2.ZxId
    transaction: _types_pb2.BankTransaction
    def __init__(self, zx_id: _Optional[_Union[_types_pb2.ZxId, _Mapping]] = ..., transaction: _Optional[_Union[_types_pb2.BankTransaction, _Mapping]] = ...) -> None: ...

class AckTransactionRequest(_message.Message):
    __slots__ = ("zx_id",)
    ZX_ID_FIELD_NUMBER: _ClassVar[int]
    zx_id: _types_pb2.ZxId
    def __init__(self, zx_id: _Optional[_Union[_types_pb2.ZxId, _Mapping]] = ...) -> None: ...

class CommitTransactionRequest(_message.Message):
    __slots__ = ("zx_id",)
    ZX_ID_FIELD_NUMBER: _ClassVar[int]
    zx_id: _types_pb2.ZxId
    def __init__(self, zx_id: _Optional[_Union[_types_pb2.ZxId, _Mapping]] = ...) -> None: ...

class UpdateHistoryOldThresholdRequest(_message.Message):
    __slots__ = ("zx_id",)
    ZX_ID_FIELD_NUMBER: _ClassVar[int]
    zx_id: _types_pb2.ZxId
    def __init__(self, zx_id: _Optional[_Union[_types_pb2.ZxId, _Mapping]] = ...) -> None: ...

class HistoryRequest(_message.Message):
    __slots__ = ("history",)
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    history: _types_pb2.History
    def __init__(self, history: _Optional[_Union[_types_pb2.History, _Mapping]] = ...) -> None: ...
