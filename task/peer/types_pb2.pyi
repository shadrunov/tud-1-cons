from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class State(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Election: _ClassVar[State]
    Following: _ClassVar[State]
    Leading: _ClassVar[State]
Election: State
Following: State
Leading: State

class ZxId(_message.Message):
    __slots__ = ("epoch", "counter")
    EPOCH_FIELD_NUMBER: _ClassVar[int]
    COUNTER_FIELD_NUMBER: _ClassVar[int]
    epoch: int
    counter: int
    def __init__(self, epoch: _Optional[int] = ..., counter: _Optional[int] = ...) -> None: ...

class Vote(_message.Message):
    __slots__ = ("id", "last_zx_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    LAST_ZX_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    last_zx_id: ZxId
    def __init__(self, id: _Optional[int] = ..., last_zx_id: _Optional[_Union[ZxId, _Mapping]] = ...) -> None: ...

class BankTransaction(_message.Message):
    __slots__ = ("account_id", "amount")
    ACCOUNT_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    account_id: int
    amount: int
    def __init__(self, account_id: _Optional[int] = ..., amount: _Optional[int] = ...) -> None: ...

class BankTransactionMapEntry(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: ZxId
    value: BankTransaction
    def __init__(self, key: _Optional[_Union[ZxId, _Mapping]] = ..., value: _Optional[_Union[BankTransaction, _Mapping]] = ...) -> None: ...

class BankTransactionMap(_message.Message):
    __slots__ = ("entries",)
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[BankTransactionMapEntry]
    def __init__(self, entries: _Optional[_Iterable[_Union[BankTransactionMapEntry, _Mapping]]] = ...) -> None: ...

class History(_message.Message):
    __slots__ = ("last_commited_zx_id", "old_threshold", "proposed", "committed")
    LAST_COMMITED_ZX_ID_FIELD_NUMBER: _ClassVar[int]
    OLD_THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    PROPOSED_FIELD_NUMBER: _ClassVar[int]
    COMMITTED_FIELD_NUMBER: _ClassVar[int]
    last_commited_zx_id: ZxId
    old_threshold: ZxId
    proposed: BankTransactionMap
    committed: BankTransactionMap
    def __init__(self, last_commited_zx_id: _Optional[_Union[ZxId, _Mapping]] = ..., old_threshold: _Optional[_Union[ZxId, _Mapping]] = ..., proposed: _Optional[_Union[BankTransactionMap, _Mapping]] = ..., committed: _Optional[_Union[BankTransactionMap, _Mapping]] = ...) -> None: ...

class Snap(_message.Message):
    __slots__ = ("db", "history")
    class DbEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: int
        def __init__(self, key: _Optional[int] = ..., value: _Optional[int] = ...) -> None: ...
    DB_FIELD_NUMBER: _ClassVar[int]
    HISTORY_FIELD_NUMBER: _ClassVar[int]
    db: _containers.ScalarMap[int, int]
    history: History
    def __init__(self, db: _Optional[_Mapping[int, int]] = ..., history: _Optional[_Union[History, _Mapping]] = ...) -> None: ...

class Diff(_message.Message):
    __slots__ = ("transactions",)
    TRANSACTIONS_FIELD_NUMBER: _ClassVar[int]
    transactions: BankTransactionMap
    def __init__(self, transactions: _Optional[_Union[BankTransactionMap, _Mapping]] = ...) -> None: ...

class Trunc(_message.Message):
    __slots__ = ("last_commited_zx_id",)
    LAST_COMMITED_ZX_ID_FIELD_NUMBER: _ClassVar[int]
    last_commited_zx_id: ZxId
    def __init__(self, last_commited_zx_id: _Optional[_Union[ZxId, _Mapping]] = ...) -> None: ...
