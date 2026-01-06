from typing import Protocol

from core.entities.run import Run


class RunRepository(Protocol):
    def add(self, run: Run) -> Run: ...

    def update(self, run: Run) -> Run: ...

    def get(self, id: str) -> Run | None: ...

    def list_all(self, limit: int = 1000) -> list[Run]: ...

    def search(
        self,
        status: str | None = None,
        id_pattern: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> tuple[list[Run], int]: ...
