from app.services.prompts import GlossaryPromptTerm, build_translation_prompt


def test_translation_prompt_includes_glossary_terms():
    prompt = build_translation_prompt(
        source_text="We use embedding vectors.",
        context_before="",
        context_after="",
        glossary=[
            GlossaryPromptTerm(source_term="embedding", target_term="嵌入", keep_english=False),
            GlossaryPromptTerm(source_term="Transformer", target_term="Transformer", keep_english=True),
        ],
    )

    assert "embedding -> 嵌入" in prompt
    assert "Transformer -> keep English term Transformer" in prompt
    assert "We use embedding vectors." in prompt
