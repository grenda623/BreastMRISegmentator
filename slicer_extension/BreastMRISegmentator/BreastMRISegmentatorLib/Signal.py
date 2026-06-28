"""A minimal observer/signal helper (no Qt dependency).

Equivalent in spirit to DentalSegmentatorLib.Signal — lets the logic layer
notify the widget about progress/finish/error without importing Qt.
"""
from __future__ import annotations

from typing import Callable


class Signal:
    def __init__(self, *_args):
        self._slots: list[Callable] = []

    def connect(self, slot: Callable) -> None:
        if slot not in self._slots:
            self._slots.append(slot)

    def disconnect(self, slot: Callable) -> None:
        if slot in self._slots:
            self._slots.remove(slot)

    def emit(self, *args, **kwargs) -> None:
        for slot in list(self._slots):
            slot(*args, **kwargs)
