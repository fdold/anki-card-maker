from domain.models import GenerationRun


class InMemoryRunRepository:
    """Temporary repository until persistent storage is introduced."""

    def __init__(self) -> None:
        self._runs: dict[str, GenerationRun] = {}

    def save(self, run: GenerationRun) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: str) -> GenerationRun | None:
        return self._runs.get(run_id)

    def list(self) -> list[GenerationRun]:
        return list(self._runs.values())

    def update(self, run: GenerationRun) -> None:
        if run.run_id not in self._runs:
            raise ValueError(f"Unknown run: {run.run_id}")
        self._runs[run.run_id] = run
