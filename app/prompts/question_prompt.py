"""Prompt templates for AI question generation."""

import json
from typing import Any

from app.schemas.question_schema import GenerateQuestionsRequest, QuestionType


def _type_plan(payload: GenerateQuestionsRequest) -> list[QuestionType]:
    n = payload.number_of_questions
    base: list[QuestionType] = list(payload.question_types) if payload.question_types else [payload.question_type]
    return [base[(payload.question_type_offset + i) % len(base)] for i in range(n)]


def _type_instructions_map() -> dict[str, str]:
    return {
        "mcq": (
            "Exactly four strings in `options` (A–D order). Distractors must be plausible and clearly wrong. "
            "Do NOT copy neighbouring bullet points as options. Paraphrase concepts into full sentences. "
            "`correct_answer` MUST equal one of the four option strings exactly (verbatim). "
            "Never use options like \"All of the above\" / \"None of the above\"."
        ),
        "fill_in": (
            "One sentence or short paragraph with ONE clear blank (use ________ in the question text). "
            "`options` must be an empty array. `correct_answer` is the short phrase that fills the blank (1–6 words)."
        ),
        "short_answer": (
            "Requires a concise factual answer (1–3 sentences expected from the student). "
            "`options` must be an empty array. `correct_answer` is the ideal short reference answer."
        ),
        "theory": (
            "Requires extended reasoning or analysis (essay-style). "
            "`options` must be an empty array. `correct_answer` is a concise model outline / key points "
            "(bullet-style in a single string is acceptable) that an instructor could use to mark."
        ),
    }


def build_question_generation_messages(payload: GenerateQuestionsRequest) -> list[dict[str, Any]]:
    """
    Build chat messages that force JSON output aligned with university assessment quality.

    The model must return a single JSON object: {"questions": [ ... ]}.
    """
    type_plan = _type_plan(payload)
    type_instructions = _type_instructions_map()

    spec_item = {
        "question": "string",
        "question_type": "mcq|fill_in|short_answer|theory",
        "options": ["string", "..."],
        "correct_answer": "string",
        "explanation": "string — why the answer is correct; 2–4 sentences; cite the note concept.",
    }

    spec = {"questions": [spec_item]}

    notes_block = ""
    if payload.lecture_notes:
        notes_block = (
            "\nGrounding rule: every question MUST be answerable ONLY from the lecture notes below. "
            "Do not invent facts that are not supported by the notes. "
            "If the notes are thin on a subtopic, ask simpler questions on what IS present.\n"
            "<<<LECTURE_NOTES>>>\n"
            f"{payload.lecture_notes}\n"
            "<<<END_LECTURE_NOTES>>>\n"
        )
    else:
        notes_block = (
            "\nNo lecture notes were supplied: generate fair questions from the course/topic only, "
            "using widely accepted definitions (still avoid ambiguity).\n"
        )

    learning_block = ""
    if payload.learning_outcome:
        learning_block = f"\nLearning outcome to align with: {payload.learning_outcome}\n"

    plan_lines = "\n".join(
        f"- Question {i + 1} (global index {payload.question_type_offset + i + 1}): MUST be `{t}` — "
        f"{type_instructions[t]}"
        for i, t in enumerate(type_plan)
    )

    system = f"""You are a senior university examiner and learning scientist.
You author fair, unambiguous assessment items aligned to Bloom's taxonomy (emphasis: apply/analyse for medium/hard; remember/understand for easy).

Rules:
- Match difficulty "{payload.difficulty}" consistently across all items.
- Course context: {payload.course}. Topic focus: {payload.topic}.
{learning_block}
{notes_block}
Per-question type plan for THIS batch (follow exactly; set each item's `question_type` to match):
{plan_lines}

Global rules:
- Avoid trick questions, ambiguous wording, and \"all of the above\" / \"none of the above\".
- For MCQ: write a specific question stem (not the generic \"Which statement best reflects the lecture content?\" unless the notes truly require it). Prefer stems that name the concept being tested.
- Use inclusive, neutral language.
- Return ONLY valid JSON (no markdown fences) with this top-level shape: {json.dumps(spec, indent=2)}
- The array `questions` must contain exactly {payload.number_of_questions} objects, in order.
- Each object's `question_type` must match the plan line for that position.
"""

    user = (
        f"Generate {payload.number_of_questions} assessment item(s) for the course \"{payload.course}\" "
        f"on the topic \"{payload.topic}\" at {payload.difficulty} difficulty, following the type plan in the system message."
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
