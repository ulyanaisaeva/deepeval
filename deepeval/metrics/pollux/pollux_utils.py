from __future__ import annotations

import re
from typing import Dict, Tuple, Union

RubricsInput = Dict[Union[int, str], str]

_RESULT_RE = re.compile(
    r"\[RESULT\]\s*([^\s\[]+)\s*\[END\]", re.IGNORECASE | re.DOTALL
)
_FEEDBACK_RE = re.compile(
    r"\[FEEDBACK\](.*?)\[RESULT\]", re.IGNORECASE | re.DOTALL
)


def build_pollux_prompt(
    instruction: str,
    answer: str,
    criteria_name: str,
    rubrics: str,
    reference_answer: str | None = None,
) -> str:
    sections = [
        "### Задание для оценки:\n" + instruction,
    ]

    if reference_answer is not None and reference_answer.strip():
        sections.append("### Эталонный ответ:\n" + reference_answer)

    sections.extend(
        [
            "### Ответ для оценки:\n" + answer,
            "### Критерий оценки:\n" + criteria_name,
            "### Шкала оценивания по критерию:\n" + rubrics,
        ]
    )
    return "\n\n".join(sections)


def parse_score(response: str) -> float | None:
    if not response:
        return None

    match = _RESULT_RE.search(response)
    if not match:
        return None

    raw = match.group(1).strip().replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_feedback(response: str) -> str:
    if not response:
        return ""

    match = _FEEDBACK_RE.search(response)
    return match.group(1).strip() if match else ""


def normalize_rubrics(rubrics: RubricsInput) -> Tuple[str, list[int]]:
    if not isinstance(rubrics, dict):
        raise ValueError(
            "rubrics must be a dictionary like {0: '...', 1: '...'}"
        )
    if len(rubrics) < 2:
        raise ValueError("rubrics must contain at least two score levels")

    normalized_pairs: list[tuple[int, str]] = []
    for key, value in rubrics.items():
        if isinstance(key, bool):
            raise ValueError("rubrics keys must be integers or numeric strings")
        if isinstance(key, int):
            numeric_key = key
        elif isinstance(key, str) and key.strip().isdigit():
            numeric_key = int(key.strip())
        else:
            raise ValueError("rubrics keys must be integers or numeric strings")

        if not isinstance(value, str) or not value.strip():
            raise ValueError("rubrics values must be non-empty strings")

        normalized_pairs.append((numeric_key, value.strip()))

    normalized_pairs.sort(key=lambda item: item[0])
    normalized_text = "\n".join(
        f"{score}: {text}" for score, text in normalized_pairs
    )
    sorted_keys = [score for score, _ in normalized_pairs]
    return normalized_text, sorted_keys
