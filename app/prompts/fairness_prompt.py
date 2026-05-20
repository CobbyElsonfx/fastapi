"""System + user messages for exam fairness JSON analysis."""

from __future__ import annotations

import json
from typing import Any

from app.schemas.fairness_schema import AnalyzeExamFairnessRequest


def build_fairness_messages(body: AnalyzeExamFairnessRequest) -> list[dict[str, Any]]:
    topics_note = (
        "The `topics` array is the official syllabus/topic list when provided. "
        "If it is empty, you MUST set each question's `syllabus_alignment` to exactly "
        "`Unknown` — do not invent topics."
    )
    system = f"""You are a university assessment quality reviewer, curriculum expert, \
instructional designer, and experienced lecturer.

Analyze the entire exam for fairness, clarity, cognitive load, and alignment with the \
given topics (when provided).

{topics_note}

For each question, assess:
1) ambiguity (unclear scope or wording)
2) excessive difficulty relative to marks and peer questions
3) syllabus/topic mismatch (use Unknown alignment if no topics list)
4) repeated question patterns across the paper
5) bias or unfair assumptions
6) trick-question wording
7) estimated solving time in minutes (realistic for a prepared student)
8) Bloom taxonomy level (Remember, Understand, Apply, Analyze, Evaluate, Create)
9) cognitive difficulty label (Easy, Medium, Hard, Very Hard)

Return ONLY valid JSON matching this exact structure (no markdown, no prose outside JSON):
{{
  "fairness_score": <integer 0-100>,
  "overall_status": "<string: e.g. Excellent|Good|Fair|Needs improvement>",
  "estimated_total_duration_minutes": <integer, sum of per-question estimates rounded>,
  "duration_status": "<Fair|Too long|Too short|Unknown relative to expected_duration_minutes>",
  "difficulty_distribution": {{
    "easy": <number 0-100>, "medium": <number>, "hard": <number>, "very_hard": <number>
  }},
  "blooms_distribution": {{
    "remember": <0-100>, "understand": <0-100>, "apply": <0-100>,
    "analyze": <0-100>, "evaluate": <0-100>, "create": <0-100>
  }},
  "cognitive_difficulty_map": [
    {{
      "question_number": <int>,
      "difficulty": "<Easy|Medium|Hard|Very Hard>",
      "blooms_level": "<Remember|Understand|Apply|Analyze|Evaluate|Create>",
      "estimated_time_minutes": <number>
    }}
  ],
  "question_analysis": [
    {{
      "question_id": <int>,
      "question_number": <int>,
      "question": "<full stem text>",
      "difficulty": "<Easy|Medium|Hard|Very Hard>",
      "blooms_level": "<Bloom level>",
      "estimated_time_minutes": <number>,
      "syllabus_alignment": "<Fully aligned|Partially aligned|Misaligned|Unknown>",
      "ambiguity_detected": <bool>,
      "excessive_difficulty": <bool>,
      "repeated_pattern": <bool>,
      "bias_detected": <bool>,
      "trick_question_detected": <bool>,
      "issues": [
        {{
          "type": "<ambiguity|difficulty|syllabus|repetition|bias|trick|timing|other>",
          "severity": "<low|medium|high>",
          "message": "<specific constructive message>",
          "suggestion": "<actionable rewrite or pedagogy tip>"
        }}
      ],
      "improved_question": "<rewritten question text if helpful, else empty string>"
    }}
  ],
  "recommendations": ["<short bullet>", "..."]
}}

Rules:
- difficulty_distribution and blooms_distribution should be percentage-like numbers \
that ideally sum to ~100 each (minor rounding ok).
- Be constructive and professional; never insult the lecturer.
- If options are null/empty for non-MCQ, use an empty array in analysis where relevant.
- Do not include markdown fences or keys outside this schema."""

    payload = {
        "exam_id": body.exam_id,
        "exam_title": body.exam_title,
        "course": body.course,
        "expected_duration_minutes": body.expected_duration_minutes,
        "topics": body.topics,
        "questions": [q.model_dump() for q in body.questions],
    }
    user = (
        "Analyze this exam JSON and respond with ONLY the JSON object described above.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
