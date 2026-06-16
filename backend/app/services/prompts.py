from dataclasses import dataclass


@dataclass(frozen=True)
class GlossaryPromptTerm:
    source_term: str
    target_term: str
    keep_english: bool = False


def glossary_lines(glossary: list[GlossaryPromptTerm]) -> str:
    if not glossary:
        return "No glossary terms are configured."
    lines: list[str] = []
    for term in glossary:
        if term.keep_english:
            lines.append(f"- {term.source_term} -> keep English term {term.source_term}")
        else:
            lines.append(f"- {term.source_term} -> {term.target_term}")
    return "\n".join(lines)


def build_translation_prompt(
    source_text: str,
    context_before: str,
    context_after: str,
    glossary: list[GlossaryPromptTerm],
) -> str:
    return f"""Translate the following academic paper paragraph into clear Simplified Chinese.
Preserve technical accuracy, citations, equations, and variable names.

Glossary:
{glossary_lines(glossary)}

Previous context:
{context_before or "None"}

Paragraph:
{source_text}

Next context:
{context_after or "None"}

Return only the translated Chinese paragraph."""
