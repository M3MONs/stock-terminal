from enum import StrEnum

TABLE_ID = "stock-table"
EMPTY_ID = "stock-empty"


class WorkerKind(StrEnum):
    META = "meta"
    SIGNAL = "signal"

    @property
    def require_result(self) -> bool:
        return self is WorkerKind.META


COL_SYMBOL = "Symbol"
COL_PRICE = "Price"
COL_CHANGE = "Change"
COL_SIGNAL = "Signal"
COL_AGE = "Age"
COL_SL = "SL"
COL_TP = "TP"

KEY_SYMBOL = "symbol"
KEY_PRICE = "price"
KEY_CHANGE = "change"
KEY_SIGNAL = "signal"
KEY_AGE = "age"
KEY_SL = "sl"
KEY_TP = "tp"

COLUMN_WEIGHTS: dict[str, int] = {
    KEY_SYMBOL: 3,
    KEY_PRICE: 3,
    KEY_CHANGE: 2,
    KEY_SIGNAL: 2,
    KEY_AGE: 2,
    KEY_SL: 2,
    KEY_TP: 2,
}

SIGNAL_STAGGER_SECONDS = 5.0
