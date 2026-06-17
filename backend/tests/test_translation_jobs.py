import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.db.models import Document, TranslationJob
from app.main import app
from app.services.translations import get_translation_job


def test_get_translation_job_returns_progress_counts(db_session):
    document = Document(title="Paper", original_filename="paper.pdf", file_path="/tmp/paper.pdf", status="parsed")
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    job = TranslationJob(
        document_id=document.id,
        status="running",
        total_count=4,
        completed_count=2,
        failed_count=1,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    result = get_translation_job(db_session, job.id)

    assert result.id == job.id
    assert result.status == "running"
    assert result.total_count == 4
    assert result.completed_count == 2
    assert result.failed_count == 1


def test_get_translation_job_raises_for_missing_job(db_session):
    with pytest.raises(ValueError, match="Translation job not found"):
        get_translation_job(db_session, 999)


def test_get_translation_job_endpoint_returns_progress(db_session):
    document = Document(title="Paper", original_filename="paper.pdf", file_path="/tmp/paper.pdf", status="parsed")
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    job = TranslationJob(document_id=document.id, status="running", total_count=3, completed_count=1, failed_count=0)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).get(f"/api/translations/jobs/{job.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "job_id": job.id,
        "document_id": document.id,
        "status": "running",
        "total_count": 3,
        "completed_count": 1,
        "failed_count": 0,
    }
