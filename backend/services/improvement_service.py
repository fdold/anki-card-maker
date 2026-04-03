import logging
from uuid import uuid4

from backend.storage.run_repository import InMemoryRunRepository
from domain.models import (
    GenerationRun,
    ImprovementAction,
    ImprovementBatch,
    ImprovementRecord,
    RunCard,
    utc_now,
)

logger = logging.getLogger(__name__)


class ImprovementService:
    def __init__(self, run_repository: InMemoryRunRepository) -> None:
        self._run_repository = run_repository

    def apply_improvements(self, batch: ImprovementBatch) -> GenerationRun:
        run = self._run_repository.get(batch.run_id)
        if run is None:
            raise ValueError(f"Unknown run: {batch.run_id}")

        logger.info(
            "Applying %s improvements to run %s",
            len(batch.actions),
            batch.run_id,
        )
        updated_run = run
        records: list[ImprovementRecord] = list(updated_run.improvement_history)
        for action in batch.actions:
            updated_run, record = self._apply_action(updated_run, action)
            records.append(record)

        completed_at = utc_now()
        updated_run = updated_run.model_copy(
            update={
                "improvement_history": records,
                "updated_at": completed_at,
            }
        )
        self._run_repository.update(updated_run)
        return updated_run

    def _apply_action(
        self,
        run: GenerationRun,
        action: ImprovementAction,
    ) -> tuple[GenerationRun, ImprovementRecord]:
        if action.action_type == "edit_card":
            return self._edit_card(run, action)
        if action.action_type == "delete_card":
            return self._delete_card(run, action)
        if action.action_type == "rate_card":
            return self._rate_card(run, action)
        if action.action_type == "rate_run":
            return self._rate_run(run, action)
        raise ValueError(f"Unsupported improvement action: {action.action_type}")

    def _edit_card(
        self,
        run: GenerationRun,
        action: ImprovementAction,
    ) -> tuple[GenerationRun, ImprovementRecord]:
        if action.card_id is None:
            raise ValueError("Action 'edit_card' requires a card_id.")
        if action.front is None and action.back is None:
            raise ValueError("Action 'edit_card' requires a front or back update.")

        card = self._get_required_card(run, action.card_id)
        updated_card = card.model_copy(
            update={
                "front": action.front if action.front is not None else card.front,
                "back": action.back if action.back is not None else card.back,
                "status": "edited",
                "updated_at": utc_now(),
            }
        )
        updated_run = self._replace_card(run, updated_card)
        return updated_run, ImprovementRecord(
            record_id=str(uuid4()),
            run_id=run.run_id,
            action_type=action.action_type,
            card_id=action.card_id,
            summary=f"Edited card {action.card_id}",
        )

    def _delete_card(
        self,
        run: GenerationRun,
        action: ImprovementAction,
    ) -> tuple[GenerationRun, ImprovementRecord]:
        if action.card_id is None:
            raise ValueError("Action 'delete_card' requires a card_id.")

        card = self._get_required_card(run, action.card_id)
        updated_card = card.model_copy(
            update={
                "status": "deleted",
                "updated_at": utc_now(),
            }
        )
        updated_run = self._replace_card(run, updated_card)
        return updated_run, ImprovementRecord(
            record_id=str(uuid4()),
            run_id=run.run_id,
            action_type=action.action_type,
            card_id=action.card_id,
            summary=f"Deleted card {action.card_id}",
        )

    def _rate_card(
        self,
        run: GenerationRun,
        action: ImprovementAction,
    ) -> tuple[GenerationRun, ImprovementRecord]:
        if action.card_id is None:
            raise ValueError("Action 'rate_card' requires a card_id.")
        if action.rating is None:
            raise ValueError("Action 'rate_card' requires a rating.")

        card = self._get_required_card(run, action.card_id)
        updated_card = card.model_copy(
            update={
                "rating": action.rating,
                "updated_at": utc_now(),
            }
        )
        updated_run = self._replace_card(run, updated_card)
        return updated_run, ImprovementRecord(
            record_id=str(uuid4()),
            run_id=run.run_id,
            action_type=action.action_type,
            card_id=action.card_id,
            summary=f"Rated card {action.card_id} as {action.rating}",
        )

    def _rate_run(
        self,
        run: GenerationRun,
        action: ImprovementAction,
    ) -> tuple[GenerationRun, ImprovementRecord]:
        if action.rating is None:
            raise ValueError("Action 'rate_run' requires a rating.")

        updated_run = run.model_copy(
            update={
                "rating": action.rating,
                "updated_at": utc_now(),
            }
        )
        return updated_run, ImprovementRecord(
            record_id=str(uuid4()),
            run_id=run.run_id,
            action_type=action.action_type,
            summary=f"Rated run {run.run_id} as {action.rating}",
        )

    def _get_required_card(self, run: GenerationRun, card_id: str) -> RunCard:
        for card in run.cards:
            if card.card_id == card_id:
                return card
        raise ValueError(f"Unknown card '{card_id}' for run '{run.run_id}'")

    def _replace_card(self, run: GenerationRun, updated_card: RunCard) -> GenerationRun:
        updated_cards = [
            updated_card if card.card_id == updated_card.card_id else card
            for card in run.cards
        ]
        return run.model_copy(update={"cards": updated_cards, "updated_at": utc_now()})
