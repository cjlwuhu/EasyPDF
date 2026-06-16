from app.db.models import ParagraphStatus


def test_paragraph_status_values_match_reader_workflow():
    assert [item.value for item in ParagraphStatus] == [
        "pending",
        "translating",
        "translated",
        "failed",
        "corrected",
    ]
