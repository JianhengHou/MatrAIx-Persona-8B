"""A model answer that does not fit the questionnaire fails the trial instead of being replaced."""

from __future__ import annotations

import pytest

pytest.importorskip("backend")

from backend.service.survey_types import SurveyInstrument, SurveyQuestion  # noqa: E402
from playground.inprocess.survey_eval import (  # noqa: E402
    SurveyAnswerError,
    _normalize_answers,
)
from playground.openai_client import openai_model_supports_custom_temperature  # noqa: E402


def _instrument() -> SurveyInstrument:
    return SurveyInstrument(
        id="s",
        title="S",
        description="",
        questions=[
            SurveyQuestion.from_dict({
                "id": "open",
                "prompt": "Would you open it?",
                "type": "single_choice",
                "options": [{"id": "yes", "label": "Ja, jeg ville åbne den"}, {"id": "no", "label": "Nej"}],
            }),
            SurveyQuestion(id="stars", prompt="Stars?", type="likert", min_value=1, max_value=5),
        ],
    )


def _values(raw: list[dict]) -> dict:
    return {a.question_id: a.value for a in _normalize_answers(raw, _instrument())}


def test_valid_answers_pass_through() -> None:
    assert _values([{"questionId": "open", "value": "no"}, {"questionId": "stars", "value": 4}]) == {
        "open": "no", "stars": 4,
    }


def test_an_option_given_by_case_or_label_maps_to_its_id() -> None:
    assert _values([{"questionId": "open", "value": "NO"}, {"questionId": "stars", "value": "4"}])["open"] == "no"
    assert _values([{"questionId": "open", "value": "Ja, jeg ville åbne den"}, {"questionId": "stars", "value": 4.0}]) == {
        "open": "yes", "stars": 4,
    }


@pytest.mark.parametrize(
    "raw, message",
    [
        ([{"questionId": "open", "value": "maybe"}, {"questionId": "stars", "value": 4}], "'maybe' is not one of the options"),
        ([{"questionId": "open", "value": "yes"}, {"questionId": "stars", "value": 3.5}], "not a whole number from 1 to 5"),
        ([{"questionId": "open", "value": "yes"}, {"questionId": "stars", "value": 9}], "not a whole number from 1 to 5"),
        ([{"questionId": "open", "value": "yes"}, {"questionId": "stars", "value": "lots"}], "not a number from 1 to 5"),
        ([{"questionId": "open", "value": "yes"}], "no answer for stars"),
    ],
)
def test_an_answer_that_does_not_fit_raises_instead_of_being_replaced(raw: list[dict], message: str) -> None:
    with pytest.raises(SurveyAnswerError, match=message):
        _normalize_answers(raw, _instrument())


def test_output_without_an_answers_list_raises() -> None:
    with pytest.raises(SurveyAnswerError, match="no answers list"):
        _normalize_answers(None, _instrument())


@pytest.mark.parametrize(
    "model, supported",
    [
        ("anthropic/claude-opus-4-1", True),
        ("claude-opus-4-20250514", True),
        ("anthropic/claude-opus-4-7", False),
        ("claude-opus-4-8", False),
        ("anthropic/claude-opus-5", False),
        ("claude-opus-5-5", False),
        ("claude-opus-5-20261001", False),
        ("anthropic/claude-sonnet-4-6", True),
        ("openai/gpt-6-sol", False),
        ("openai/gpt-4o", True),
    ],
)
def test_temperature_is_left_out_for_opus_4_7_and_later(model: str, supported: bool) -> None:
    assert openai_model_supports_custom_temperature(model) is supported
