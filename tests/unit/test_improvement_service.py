from backend.services.document_service import DocumentService
from backend.services.improvement_service import ImprovementService
from backend.services.run_service import RunService
from backend.storage.document_repository import InMemoryDocumentRepository
from backend.storage.run_repository import InMemoryRunRepository
from domain.models import ImprovementAction, ImprovementBatch


def _create_run_with_cards():
    document_repository = InMemoryDocumentRepository()
    run_repository = InMemoryRunRepository()
    document_service = DocumentService(document_repository=document_repository)
    run_service = RunService(
        document_repository=document_repository,
        run_repository=run_repository,
    )
    improvement_service = ImprovementService(run_repository=run_repository)

    stored_document = document_service.upload_document(
        filename="biology.txt",
        content="Cells are the basic unit of life.\n\nDNA stores genetic information.",
        document_id="doc-1",
    )
    generation_run = run_service.create_run(
        document_ids=[stored_document.document_id],
        workflow_plugin_id="basic_text_workflow",
        workflow_config={"max_cards": 5},
    )
    return generation_run, improvement_service, run_repository


def test_improvement_service_applies_edit_delete_and_rating_actions() -> None:
    generation_run, improvement_service, run_repository = _create_run_with_cards()
    first_card = generation_run.cards[0]
    second_card = generation_run.cards[1]

    updated_run = improvement_service.apply_improvements(
        ImprovementBatch(
            run_id=generation_run.run_id,
            actions=[
                ImprovementAction(
                    action_type="edit_card",
                    card_id=first_card.card_id,
                    front="What are cells?",
                    back="Cells are the smallest basic units of life.",
                ),
                ImprovementAction(
                    action_type="rate_card",
                    card_id=first_card.card_id,
                    rating="good",
                ),
                ImprovementAction(
                    action_type="delete_card",
                    card_id=second_card.card_id,
                ),
                ImprovementAction(
                    action_type="rate_run",
                    rating="mixed",
                ),
            ],
        )
    )

    edited_card = next(card for card in updated_run.cards if card.card_id == first_card.card_id)
    deleted_card = next(card for card in updated_run.cards if card.card_id == second_card.card_id)

    assert edited_card.front == "What are cells?"
    assert edited_card.back == "Cells are the smallest basic units of life."
    assert edited_card.original_front != edited_card.front
    assert edited_card.status == "edited"
    assert edited_card.rating == "good"
    assert deleted_card.status == "deleted"
    assert updated_run.rating == "mixed"
    assert len(updated_run.improvement_history) == 4
    assert run_repository.get(updated_run.run_id) == updated_run


def test_improvement_service_rejects_unknown_runs() -> None:
    improvement_service = ImprovementService(run_repository=InMemoryRunRepository())

    try:
        improvement_service.apply_improvements(
            ImprovementBatch(
                run_id="missing-run",
                actions=[ImprovementAction(action_type="rate_run", rating="good")],
            )
        )
    except ValueError as exc:
        assert str(exc) == "Unknown run: missing-run"
    else:
        raise AssertionError("Expected ValueError for unknown runs.")


def test_improvement_service_rejects_invalid_card_actions() -> None:
    generation_run, improvement_service, _run_repository = _create_run_with_cards()

    try:
        improvement_service.apply_improvements(
            ImprovementBatch(
                run_id=generation_run.run_id,
                actions=[ImprovementAction(action_type="edit_card", card_id=generation_run.cards[0].card_id)],
            )
        )
    except ValueError as exc:
        assert str(exc) == "Action 'edit_card' requires a front or back update."
    else:
        raise AssertionError("Expected ValueError for incomplete edit action.")

    try:
        improvement_service.apply_improvements(
            ImprovementBatch(
                run_id=generation_run.run_id,
                actions=[ImprovementAction(action_type="rate_card", card_id="missing-card", rating="bad")],
            )
        )
    except ValueError as exc:
        assert str(exc) == f"Unknown card 'missing-card' for run '{generation_run.run_id}'"
    else:
        raise AssertionError("Expected ValueError for unknown cards.")


def test_improvement_service_applies_plugin_refinement_to_selected_cards() -> None:
    generation_run, improvement_service, _run_repository = _create_run_with_cards()
    first_card = generation_run.cards[0]
    second_card = generation_run.cards[1]

    updated_run = improvement_service.apply_improvements(
        ImprovementBatch(
            run_id=generation_run.run_id,
            actions=[
                ImprovementAction(
                    action_type="prompt_refine_selected",
                    card_ids=[first_card.card_id],
                    prompt="Make this more concise and keep it a question",
                )
            ],
        )
    )

    refined_first_card = next(card for card in updated_run.cards if card.card_id == first_card.card_id)
    untouched_second_card = next(card for card in updated_run.cards if card.card_id == second_card.card_id)

    assert refined_first_card.front.endswith("?")
    assert refined_first_card.back == "Cells are the basic unit of life."
    assert refined_first_card.status == "edited"
    assert "improved" in refined_first_card.tags
    assert untouched_second_card.back == second_card.back
    assert updated_run.improvement_history[-1].action_type == "prompt_refine_selected"


def test_improvement_service_applies_plugin_refinement_to_all_active_cards() -> None:
    generation_run, improvement_service, _run_repository = _create_run_with_cards()

    updated_run = improvement_service.apply_improvements(
        ImprovementBatch(
            run_id=generation_run.run_id,
            actions=[
                ImprovementAction(
                    action_type="prompt_refine_all",
                    prompt="Keep it a question",
                )
            ],
        )
    )

    assert all(card.front.endswith("?") for card in updated_run.cards)
    assert all("improved" in card.tags for card in updated_run.cards)


def test_improvement_service_rejects_invalid_plugin_refinement_requests() -> None:
    generation_run, improvement_service, _run_repository = _create_run_with_cards()

    try:
        improvement_service.apply_improvements(
            ImprovementBatch(
                run_id=generation_run.run_id,
                actions=[
                    ImprovementAction(
                        action_type="prompt_refine_selected",
                        prompt="Make this more concise",
                    )
                ],
            )
        )
    except ValueError as exc:
        assert str(exc) == "Action 'prompt_refine_selected' requires at least one target card."
    else:
        raise AssertionError("Expected ValueError for missing selected target cards.")

    try:
        improvement_service.apply_improvements(
            ImprovementBatch(
                run_id=generation_run.run_id,
                actions=[
                    ImprovementAction(
                        action_type="prompt_refine_all",
                        prompt="   ",
                    )
                ],
            )
        )
    except ValueError as exc:
        assert str(exc) == "Action 'prompt_refine_all' requires a non-empty prompt."
    else:
        raise AssertionError("Expected ValueError for empty refinement prompts.")
