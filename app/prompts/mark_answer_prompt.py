"""Prompts for concept-based script marking."""

from __future__ import annotations


def build_mark_answer_messages(
    *,
    question_text: str,
    student_answer: str,
    max_marks: int,
    question_type: str,
    model_answer: str | None,
) -> list[dict[str, str]]:
    model_block = (
        f"\nExpected / model answer (reference): {model_answer}"
        if model_answer and model_answer.strip()
        else ""
    )

    if question_type == "fill_in":
        user = f"""You are an exam marker. This is a SHORT fill-in answer; award full marks only for answers that match the expected meaning; allow minor wording differences.

Question: {question_text}
Maximum marks: {max_marks}
{model_block}

Student response:
{student_answer}

Reply with ONE JSON object only, using these keys:
- "marks_awarded" (number, 0 to {max_marks}, can be fractional with one decimal)
- "confidence" (number 0 to 1)
- "evaluation_status": one of "correct", "partial", "incorrect", "unanswered"
- "detected_concepts": array of short strings
- "missing_concepts": array of short strings
- "reason": one or two sentences explaining the mark
- "feedback": one sentence advice for the student

If the response is blank or irrelevant, use marks_awarded 0 and evaluation_status "unanswered"."""
        system = (
            "You are an exam marker. Reply with a single JSON object only (no markdown fences)."
        )
    else:
        user = f"""You are a fair university examiner marking a THEORY answer. Your job is CONCEPT COVERAGE, not matching exact sentences.

Rules:
1. Infer 4–8 distinct key concepts a strong answer should cover. Output them in "key_concepts_rubric".
2. Treat synonyms and paraphrases as valid when the student shows understanding.
3. Award "marks_awarded" proportionally (0 to {max_marks}). Use 0.5 mark steps.
4. Set "concept_coverage" between 0 and 1.
5. Use "partial" when understanding is real but incomplete.
6. Do NOT give marks_awarded = 0 if at least one relevant concept appears in "detected_concepts" (unless off-topic).

Question: {question_text}
Maximum marks: {max_marks}
{model_block}

Student response:
{student_answer}

Reply with ONE JSON object only, using these keys:
- "marks_awarded" (number, 0 to {max_marks}, step 0.5)
- "confidence" (number 0 to 1)
- "concept_coverage" (number 0 to 1)
- "evaluation_status": one of "correct", "partial", "incorrect", "unanswered"
- "key_concepts_rubric": array of short strings
- "detected_concepts": array of short strings
- "missing_concepts": array of short strings
- "reason": one or two sentences
- "feedback": one sentence advice

If blank or completely unrelated, use marks_awarded 0, concept_coverage 0, evaluation_status "unanswered"."""
        system = (
            "You are a fair university examiner marking THEORY answers. "
            "Reward conceptual understanding and synonyms. Reply with ONE JSON object only."
        )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
