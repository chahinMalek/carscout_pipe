from typing import Protocol

from core.entities.run import Run


class RunRepository(Protocol):
    def add(self, run: Run) -> Run: ...

    def update(self, run: Run) -> Run: ...

    def get(self, id: str) -> Run | None: ...
