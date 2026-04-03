import logging
from uuid import uuid4

from backend.services.registry import get_workflow_plugin
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import (
    GenerationRun,
    ImprovementAction,
    ImprovementBatch,
    ImprovementRecord,
    RunCard,
    WorkflowImprovementRequest,
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
        if action.action_type in {"prompt_refine_selected", "prompt_refine_all"}:
            return self._apply_plugin_improvement(run, action)
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

    def _apply_plugin_improvement(
        self,
        run: GenerationRun,
        action: ImprovementAction,
    ) -> tuple[GenerationRun, ImprovementRecord]:
        if action.prompt is None or not action.prompt.strip():
            raise ValueError(
                f"Action '{action.action_type}' requires a non-empty prompt."
            )

        workflow = get_workflow_plugin(run.plugin_id)
        if action.action_type not in workflow.manifest.supported_operations:
            raise ValueError(
                f"Workflow plugin '{run.plugin_id}' does not support "
                f"improvement action '{action.action_type}'."
            )

        selected_cards = self._get_cards_for_plugin_improvement(run, action)
        config = workflow.config_model.model_validate(run.workflow_config)
        improved_cards = workflow.apply_improvement(
            WorkflowImprovementRequest(
                action_type=action.action_type,
                run_id=run.run_id,
                prompt=action.prompt.strip(),
                cards=selected_cards,
            ),
            config,
        )

        updated_run = run
        for improved_card in improved_cards:
            updated_run = self._replace_card(updated_run, improved_card)

        summary_suffix = (
            f"{len(improved_cards)} selected cards"
            if action.action_type == "prompt_refine_selected"
            else f"{len(improved_cards)} cards"
        )
        return updated_run, ImprovementRecord(
            record_id=str(uuid4()),
            run_id=run.run_id,
            action_type=action.action_type,
            summary=(
                f"Applied workflow prompt refinement to {summary_suffix} "
                f"with plugin '{run.plugin_id}'"
            ),
        )

    def _get_required_card(self, run: GenerationRun, card_id: str) -> RunCard:
        for card in run.cards:
            if card.card_id == card_id:
                return card
        raise ValueError(f"Unknown card '{card_id}' for run '{run.run_id}'")

    def _get_cards_for_plugin_improvement(
        self,
        run: GenerationRun,
        action: ImprovementAction,
    ) -> list[RunCard]:
        if action.action_type == "prompt_refine_all":
            return [card for card in run.cards if card.status != "deleted"]

        selected_card_ids = action.card_ids or ([action.card_id] if action.card_id else [])
        if not selected_card_ids:
            raise ValueError(
                "Action 'prompt_refine_selected' requires at least one target card."
            )
        return [self._get_required_card(run, card_id) for card_id in selected_card_ids]

    def _replace_card(self, run: GenerationRun, updated_card: RunCard) -> GenerationRun:
        updated_cards = [
            updated_card if card.card_id == updated_card.card_id else card
            for card in run.cards
        ]
        return run.model_copy(update={"cards": updated_cards, "updated_at": utc_now()})
