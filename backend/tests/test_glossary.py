from app.services.glossary import create_term, delete_term, list_enabled_terms, list_terms


def test_create_and_list_enabled_terms(db_session):
    create_term(
        db_session,
        source_term="embedding",
        target_term="嵌入",
        note="machine learning term",
        keep_english=False,
    )

    terms = list_enabled_terms(db_session)

    assert len(terms) == 1
    assert terms[0].source_term == "embedding"
    assert terms[0].target_term == "嵌入"


def test_delete_term_removes_it_from_glossary(db_session):
    term = create_term(
        db_session,
        source_term="attention",
        target_term="attention-cn",
        note="transformer term",
        keep_english=False,
    )

    assert delete_term(db_session, term.id) is True

    assert list_terms(db_session) == []
