# EasyPDF MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first EasyPDF MVP with FastAPI, Vue, PDF.js, MySQL persistence, PDF upload/parsing, Chinese translation workflow, correction tools, AI Q&A, settings, and glossary management.

**Architecture:** The backend owns persistence, PDF parsing, translation orchestration, settings, and OpenAI-compatible API calls. The frontend is a Vue workbench with a document library, settings/glossary screens, and a two-pane reader where PDF.js renders the original PDF while translated paragraph data renders beside it. MySQL stores structured state; local filesystem storage holds uploaded PDFs and extracted assets.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, PyMySQL, Pydantic Settings, PyMuPDF, HTTPX, Pytest, Vue 3, Vite, TypeScript, Pinia, Vue Router, PDF.js, Vitest.

---

## File Structure

Create this structure under `D:\Project\EasyPDF`:

```text
backend/
  alembic/
    env.py
    versions/
  app/
    api/
      routes/
        assistant.py
        corrections.py
        documents.py
        glossary.py
        settings.py
        translations.py
      deps.py
      router.py
    core/
      config.py
      security.py
    db/
      base.py
      models.py
      session.py
    schemas/
      assistant.py
      corrections.py
      documents.py
      glossary.py
      settings.py
      translations.py
    services/
      ai_client.py
      documents.py
      glossary.py
      pdf_parser.py
      prompts.py
      settings.py
      translations.py
    main.py
  tests/
    conftest.py
    test_config.py
    test_glossary.py
    test_pdf_parser.py
    test_prompts.py
    test_settings_api.py
    test_translation_states.py
  alembic.ini
  pyproject.toml
  .env.example
frontend/
  index.html
  package.json
  tsconfig.json
  vite.config.ts
  src/
    App.vue
    main.ts
    router.ts
    api/client.ts
    stores/documents.ts
    stores/settings.ts
    types.ts
    components/
      AppShell.vue
      PdfPane.vue
      StatusBadge.vue
      SelectionToolbar.vue
    views/
      DocumentLibrary.vue
      ReaderView.vue
      SettingsView.vue
      GlossaryView.vue
  tests/
    reader-selection.test.ts
scripts/
  dev.ps1
  init-db.sql
```

Responsibilities:

- `backend/app/core/config.py`: load environment and local app settings.
- `backend/app/db/models.py`: SQLAlchemy entities and relationships.
- `backend/app/services/pdf_parser.py`: convert text-based PDFs into page/block/paragraph records.
- `backend/app/services/prompts.py`: construct translation, retranslation, and AI assistant prompts with glossary terms.
- `backend/app/services/translations.py`: manage paragraph translation states, initial-page priority, background document translation, and AI API calls.
- `backend/app/api/routes/*.py`: expose focused HTTP endpoints.
- `frontend/src/api/client.ts`: typed fetch wrapper for backend calls.
- `frontend/src/views/ReaderView.vue`: two-pane reader and selected-paragraph workflow.
- `frontend/src/views/SettingsView.vue`: API, model, database, and storage configuration.
- `frontend/src/views/GlossaryView.vue`: term preference CRUD.

---

## Task 1: Backend Project Skeleton And Configuration

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing config test**

Create `backend/tests/test_config.py`:

```python
from app.core.config import Settings


def test_database_url_uses_mysql_settings():
    settings = Settings(
        mysql_host="localhost",
        mysql_port=3306,
        mysql_database="easypdf",
        mysql_user="root",
        mysql_password="secret",
    )

    assert settings.database_url == "mysql+pymysql://root:secret@localhost:3306/easypdf?charset=utf8mb4"


def test_api_key_is_masked():
    settings = Settings(api_key="sk-1234567890abcdef")

    assert settings.masked_api_key == "sk-********cdef"
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
conda activate lang_chain01
cd D:\Project\EasyPDF\backend
pytest tests/test_config.py -v
```

Expected: FAIL because `app.core.config` does not exist.

- [ ] **Step 3: Add backend dependency metadata**

Create `backend/pyproject.toml`:

```toml
[project]
name = "easypdf-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.111",
  "uvicorn[standard]>=0.30",
  "sqlalchemy>=2.0",
  "alembic>=1.13",
  "pymysql>=1.1",
  "pydantic-settings>=2.3",
  "python-multipart>=0.0.9",
  "pymupdf>=1.24",
  "httpx>=0.27",
]

[project.optional-dependencies]
test = ["pytest>=8.2", "pytest-asyncio>=0.23"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 4: Add local environment example**

Create `backend/.env.example`:

```dotenv
APP_NAME=EasyPDF
APP_ENV=local

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=easypdf
MYSQL_USER=root
MYSQL_PASSWORD=

API_KEY=
BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4.1-mini

STORAGE_DIR=../storage
TRANSLATION_CONCURRENCY=2
TRANSLATION_BATCH_SIZE=6
```

- [ ] **Step 5: Implement settings**

Create `backend/app/core/config.py`:

```python
from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EasyPDF"
    app_env: str = "local"
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "easypdf"
    mysql_user: str = "root"
    mysql_password: str = ""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4.1-mini"
    storage_dir: str = "../storage"
    translation_concurrency: int = Field(default=2, ge=1, le=8)
    translation_batch_size: int = Field(default=6, ge=1, le=20)

    @cached_property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def masked_api_key(self) -> str:
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "********"
        return f"{self.api_key[:3]}-********{self.api_key[-4:]}"


settings = Settings()
```

- [ ] **Step 6: Add FastAPI entrypoint**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
```

- [ ] **Step 7: Run tests and health check**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_config.py -v
uvicorn app.main:app --port 8000
```

Expected: config tests PASS. In another terminal, `Invoke-RestMethod http://localhost:8000/health` returns `status = ok`.

- [ ] **Step 8: Commit**

```powershell
git add backend/pyproject.toml backend/.env.example backend/app/main.py backend/app/core/config.py backend/tests/test_config.py
git commit -m "feat: add backend configuration"
```

---

## Task 2: Database Models, Sessions, And Migration Baseline

**Files:**
- Create: `scripts/init-db.sql`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/20260616_0001_initial.py`
- Create: `backend/tests/test_translation_states.py`

- [ ] **Step 1: Write failing model test**

Create `backend/tests/test_translation_states.py`:

```python
from app.db.models import ParagraphStatus


def test_paragraph_status_values_match_reader_workflow():
    assert [item.value for item in ParagraphStatus] == [
        "pending",
        "translating",
        "translated",
        "failed",
        "corrected",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_translation_states.py -v
```

Expected: FAIL because `app.db.models` does not exist.

- [ ] **Step 3: Add database initialization SQL**

Create `scripts/init-db.sql`:

```sql
CREATE DATABASE IF NOT EXISTS easypdf
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

- [ ] **Step 4: Add SQLAlchemy base and session**

Create `backend/app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Create `backend/app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Add core models**

Create `backend/app/db/models.py`:

```python
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParagraphStatus(str, enum.Enum):
    pending = "pending"
    translating = "translating"
    translated = "translated"
    failed = "failed"
    corrected = "corrected"


class BlockType(str, enum.Enum):
    text = "text"
    image = "image"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512))
    original_filename: Mapped[str] = mapped_column(String(512))
    file_path: Mapped[str] = mapped_column(String(1024))
    status: Mapped[str] = mapped_column(String(64), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    pages: Mapped[list[Page]] = relationship(back_populates="document", cascade="all, delete-orphan")
    paragraphs: Mapped[list[Paragraph]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    width: Mapped[float] = mapped_column(default=0)
    height: Mapped[float] = mapped_column(default=0)

    document: Mapped[Document] = relationship(back_populates="pages")
    blocks: Mapped[list[Block]] = relationship(back_populates="page", cascade="all, delete-orphan")


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    block_type: Mapped[BlockType] = mapped_column(Enum(BlockType))
    order_index: Mapped[int] = mapped_column(Integer)
    x0: Mapped[float] = mapped_column(default=0)
    y0: Mapped[float] = mapped_column(default=0)
    x1: Mapped[float] = mapped_column(default=0)
    y1: Mapped[float] = mapped_column(default=0)
    content: Mapped[str] = mapped_column(Text, default="")
    asset_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    page: Mapped[Page] = relationship(back_populates="blocks")


class Paragraph(Base):
    __tablename__ = "paragraphs"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer, index=True)
    order_index: Mapped[int] = mapped_column(Integer)
    source_text: Mapped[str] = mapped_column(Text)
    translated_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ParagraphStatus] = mapped_column(Enum(ParagraphStatus), default=ParagraphStatus.pending)
    x0: Mapped[float] = mapped_column(default=0)
    y0: Mapped[float] = mapped_column(default=0)
    x1: Mapped[float] = mapped_column(default=0)
    y1: Mapped[float] = mapped_column(default=0)

    document: Mapped[Document] = relationship(back_populates="paragraphs")


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_term: Mapped[str] = mapped_column(String(255), unique=True)
    target_term: Mapped[str] = mapped_column(String(255))
    note: Mapped[str] = mapped_column(Text, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    keep_english: Mapped[bool] = mapped_column(Boolean, default=False)


class Correction(Base):
    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(primary_key=True)
    paragraph_id: Mapped[int] = mapped_column(ForeignKey("paragraphs.id", ondelete="CASCADE"), index=True)
    old_text: Mapped[str] = mapped_column(Text)
    new_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TranslationJob(Base):
    __tablename__ = "translation_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(64), default="queued")
    total_count: Mapped[int] = mapped_column(default=0)
    completed_count: Mapped[int] = mapped_column(default=0)
    failed_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReaderPosition(Base):
    __tablename__ = "reader_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    page_number: Mapped[int] = mapped_column(default=1)
    paragraph_id: Mapped[int | None] = mapped_column(ForeignKey("paragraphs.id", ondelete="SET NULL"), nullable=True)
    scroll_top: Mapped[int] = mapped_column(default=0)
```

- [ ] **Step 6: Add Alembic configuration**

Create `backend/alembic.ini`:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = mysql+pymysql://root:@localhost:3306/easypdf?charset=utf8mb4

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

Create `backend/alembic/env.py`:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.base import Base
from app.db import models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 7: Add initial migration**

Create `backend/alembic/versions/20260616_0001_initial.py`:

```python
from alembic import op
import sqlalchemy as sa

revision = "20260616_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    paragraph_status = sa.Enum("pending", "translating", "translated", "failed", "corrected", name="paragraphstatus")
    block_type = sa.Enum("text", "image", name="blocktype")

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "glossary_terms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_term", sa.String(length=255), nullable=False, unique=True),
        sa.Column("target_term", sa.String(length=255), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("keep_english", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.UniqueConstraint("document_id", "page_number"),
    )
    op.create_index("ix_pages_document_id", "pages", ["document_id"])
    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_type", block_type, nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("x0", sa.Float(), nullable=False),
        sa.Column("y0", sa.Float(), nullable=False),
        sa.Column("x1", sa.Float(), nullable=False),
        sa.Column("y1", sa.Float(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("asset_path", sa.String(length=1024), nullable=True),
    )
    op.create_index("ix_blocks_document_id", "blocks", ["document_id"])
    op.create_index("ix_blocks_page_id", "blocks", ["page_id"])
    op.create_table(
        "paragraphs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("status", paragraph_status, nullable=False),
        sa.Column("x0", sa.Float(), nullable=False),
        sa.Column("y0", sa.Float(), nullable=False),
        sa.Column("x1", sa.Float(), nullable=False),
        sa.Column("y1", sa.Float(), nullable=False),
    )
    op.create_index("ix_paragraphs_document_id", "paragraphs", ["document_id"])
    op.create_index("ix_paragraphs_page_number", "paragraphs", ["page_number"])
    op.create_table(
        "corrections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("paragraph_id", sa.Integer(), sa.ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_text", sa.Text(), nullable=False),
        sa.Column("new_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_corrections_paragraph_id", "corrections", ["paragraph_id"])
    op.create_table(
        "translation_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("completed_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_translation_jobs_document_id", "translation_jobs", ["document_id"])
    op.create_table(
        "reader_positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("paragraph_id", sa.Integer(), sa.ForeignKey("paragraphs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scroll_top", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reader_positions")
    op.drop_index("ix_translation_jobs_document_id", table_name="translation_jobs")
    op.drop_table("translation_jobs")
    op.drop_index("ix_corrections_paragraph_id", table_name="corrections")
    op.drop_table("corrections")
    op.drop_index("ix_paragraphs_page_number", table_name="paragraphs")
    op.drop_index("ix_paragraphs_document_id", table_name="paragraphs")
    op.drop_table("paragraphs")
    op.drop_index("ix_blocks_page_id", table_name="blocks")
    op.drop_index("ix_blocks_document_id", table_name="blocks")
    op.drop_table("blocks")
    op.drop_index("ix_pages_document_id", table_name="pages")
    op.drop_table("pages")
    op.drop_table("glossary_terms")
    op.drop_table("documents")
```

- [ ] **Step 8: Run unit test and migration**

Run:

```powershell
cd D:\Project\EasyPDF
mysql -uroot -p123456 < scripts/init-db.sql
cd backend
pytest tests/test_translation_states.py -v
alembic upgrade head
```

Expected: test PASS, Alembic upgrades MySQL database `easypdf` to revision `20260616_0001`.

- [ ] **Step 9: Commit**

```powershell
git add scripts/init-db.sql backend/app/db backend/alembic.ini backend/alembic backend/tests/test_translation_states.py
git commit -m "feat: add mysql schema"
```

---

## Task 3: Glossary Service And API

**Files:**
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/router.py`
- Create: `backend/app/api/routes/glossary.py`
- Create: `backend/app/schemas/glossary.py`
- Create: `backend/app/services/glossary.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_glossary.py`

- [ ] **Step 1: Write failing glossary service test**

Create `backend/tests/conftest.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
```

Create `backend/tests/test_glossary.py`:

```python
from app.services.glossary import create_term, list_enabled_terms


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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_glossary.py -v
```

Expected: FAIL because `app.services.glossary` does not exist.

- [ ] **Step 3: Add schemas**

Create `backend/app/schemas/glossary.py`:

```python
from pydantic import BaseModel, ConfigDict


class GlossaryTermCreate(BaseModel):
    source_term: str
    target_term: str
    note: str = ""
    keep_english: bool = False


class GlossaryTermUpdate(BaseModel):
    target_term: str | None = None
    note: str | None = None
    enabled: bool | None = None
    keep_english: bool | None = None


class GlossaryTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_term: str
    target_term: str
    note: str
    enabled: bool
    keep_english: bool
```

- [ ] **Step 4: Implement glossary service**

Create `backend/app/services/glossary.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GlossaryTerm


def create_term(
    db: Session,
    source_term: str,
    target_term: str,
    note: str = "",
    keep_english: bool = False,
) -> GlossaryTerm:
    term = GlossaryTerm(
        source_term=source_term.strip(),
        target_term=target_term.strip(),
        note=note.strip(),
        keep_english=keep_english,
        enabled=True,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


def list_terms(db: Session) -> list[GlossaryTerm]:
    return list(db.scalars(select(GlossaryTerm).order_by(GlossaryTerm.source_term)))


def list_enabled_terms(db: Session) -> list[GlossaryTerm]:
    statement = select(GlossaryTerm).where(GlossaryTerm.enabled.is_(True)).order_by(GlossaryTerm.source_term)
    return list(db.scalars(statement))
```

- [ ] **Step 5: Add dependency and route modules**

Create `backend/app/api/deps.py`:

```python
from app.db.session import get_db

__all__ = ["get_db"]
```

Create `backend/app/api/routes/glossary.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.glossary import GlossaryTermCreate, GlossaryTermRead
from app.services.glossary import create_term, list_terms

router = APIRouter(prefix="/glossary", tags=["glossary"])


@router.get("", response_model=list[GlossaryTermRead])
def get_glossary(db: Session = Depends(get_db)):
    return list_terms(db)


@router.post("", response_model=GlossaryTermRead)
def post_glossary(payload: GlossaryTermCreate, db: Session = Depends(get_db)):
    return create_term(
        db,
        source_term=payload.source_term,
        target_term=payload.target_term,
        note=payload.note,
        keep_english=payload.keep_english,
    )
```

Create `backend/app/api/router.py`:

```python
from fastapi import APIRouter

from app.api.routes import glossary

api_router = APIRouter(prefix="/api")
api_router.include_router(glossary.router)
```

- [ ] **Step 6: Include API router**

Modify `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
```

- [ ] **Step 7: Run tests**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_glossary.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add backend/app/api backend/app/schemas/glossary.py backend/app/services/glossary.py backend/app/main.py backend/tests/conftest.py backend/tests/test_glossary.py
git commit -m "feat: add glossary api"
```

---

## Task 4: PDF Parsing And Document Upload

**Files:**
- Create: `backend/app/schemas/documents.py`
- Create: `backend/app/services/pdf_parser.py`
- Create: `backend/app/services/documents.py`
- Create: `backend/app/api/routes/documents.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_pdf_parser.py`

- [ ] **Step 1: Write failing parser test**

Create `backend/tests/test_pdf_parser.py`:

```python
from pathlib import Path

import fitz

from app.services.pdf_parser import parse_pdf


def test_parse_pdf_returns_paragraphs(tmp_path: Path):
    pdf_path = tmp_path / "paper.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "This is an academic paragraph about embeddings.")
    document.save(pdf_path)
    document.close()

    result = parse_pdf(pdf_path)

    assert result.pages[0].page_number == 1
    assert result.paragraphs[0].source_text == "This is an academic paragraph about embeddings."
    assert result.paragraphs[0].page_number == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_pdf_parser.py -v
```

Expected: FAIL because `parse_pdf` does not exist.

- [ ] **Step 3: Implement parser value objects and parser**

Create `backend/app/services/pdf_parser.py`:

```python
from dataclasses import dataclass
from pathlib import Path

import fitz


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    width: float
    height: float


@dataclass(frozen=True)
class ParsedBlock:
    page_number: int
    order_index: int
    block_type: str
    content: str
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class ParsedParagraph:
    page_number: int
    order_index: int
    source_text: str
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class ParsedPdf:
    pages: list[ParsedPage]
    blocks: list[ParsedBlock]
    paragraphs: list[ParsedParagraph]


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def parse_pdf(pdf_path: Path) -> ParsedPdf:
    document = fitz.open(pdf_path)
    pages: list[ParsedPage] = []
    blocks: list[ParsedBlock] = []
    paragraphs: list[ParsedParagraph] = []

    for page_index, page in enumerate(document, start=1):
        rect = page.rect
        pages.append(ParsedPage(page_number=page_index, width=rect.width, height=rect.height))
        raw_blocks = page.get_text("blocks")
        text_order = 0
        for block in sorted(raw_blocks, key=lambda item: (item[1], item[0])):
            x0, y0, x1, y1, text, *_rest = block
            normalized = normalize_text(text)
            if not normalized:
                continue
            blocks.append(
                ParsedBlock(
                    page_number=page_index,
                    order_index=text_order,
                    block_type="text",
                    content=normalized,
                    x0=float(x0),
                    y0=float(y0),
                    x1=float(x1),
                    y1=float(y1),
                )
            )
            paragraphs.append(
                ParsedParagraph(
                    page_number=page_index,
                    order_index=text_order,
                    source_text=normalized,
                    x0=float(x0),
                    y0=float(y0),
                    x1=float(x1),
                    y1=float(y1),
                )
            )
            text_order += 1

    document.close()
    return ParsedPdf(pages=pages, blocks=blocks, paragraphs=paragraphs)
```

- [ ] **Step 4: Add document schemas**

Create `backend/app/schemas/documents.py`:

```python
from pydantic import BaseModel, ConfigDict


class ParagraphRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    page_number: int
    order_index: int
    source_text: str
    translated_text: str
    status: str
    x0: float
    y0: float
    x1: float
    y1: float


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    original_filename: str
    status: str


class DocumentDetail(DocumentRead):
    paragraphs: list[ParagraphRead]
```

- [ ] **Step 5: Implement document service**

Create `backend/app/services/documents.py`:

```python
from pathlib import Path
from shutil import copyfileobj

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Block, BlockType, Document, Page, Paragraph
from app.services.pdf_parser import parse_pdf


def storage_root() -> Path:
    root = Path(settings.storage_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_upload(file: UploadFile) -> Path:
    upload_dir = storage_root() / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / file.filename
    with destination.open("wb") as output:
        copyfileobj(file.file, output)
    return destination


def create_document_from_pdf(db: Session, file: UploadFile) -> Document:
    pdf_path = save_upload(file)
    parsed = parse_pdf(pdf_path)
    document = Document(
        title=Path(file.filename).stem,
        original_filename=file.filename,
        file_path=str(pdf_path),
        status="parsed",
    )
    db.add(document)
    db.flush()

    page_by_number: dict[int, Page] = {}
    for parsed_page in parsed.pages:
        page = Page(
            document_id=document.id,
            page_number=parsed_page.page_number,
            width=parsed_page.width,
            height=parsed_page.height,
        )
        db.add(page)
        db.flush()
        page_by_number[parsed_page.page_number] = page

    for parsed_block in parsed.blocks:
        page = page_by_number[parsed_block.page_number]
        db.add(
            Block(
                document_id=document.id,
                page_id=page.id,
                block_type=BlockType.text,
                order_index=parsed_block.order_index,
                content=parsed_block.content,
                x0=parsed_block.x0,
                y0=parsed_block.y0,
                x1=parsed_block.x1,
                y1=parsed_block.y1,
            )
        )

    for parsed_paragraph in parsed.paragraphs:
        db.add(
            Paragraph(
                document_id=document.id,
                page_number=parsed_paragraph.page_number,
                order_index=parsed_paragraph.order_index,
                source_text=parsed_paragraph.source_text,
                translated_text="",
                x0=parsed_paragraph.x0,
                y0=parsed_paragraph.y0,
                x1=parsed_paragraph.x1,
                y1=parsed_paragraph.y1,
            )
        )

    db.commit()
    db.refresh(document)
    return document


def list_documents(db: Session) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.updated_at.desc())))


def get_document(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)
```

- [ ] **Step 6: Add document routes**

Create `backend/app/api/routes/documents.py`:

```python
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.documents import DocumentDetail, DocumentRead
from app.services.documents import create_document_from_pdf, get_document, list_documents

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def get_documents(db: Session = Depends(get_db)):
    return list_documents(db)


@router.post("", response_model=DocumentRead)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    return create_document_from_pdf(db, file)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document_detail(document_id: int, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/file")
def get_document_file(document_id: int, db: Session = Depends(get_db)):
    document = get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(document.file_path, media_type="application/pdf", filename=document.original_filename)
```

Modify `backend/app/api/router.py`:

```python
from fastapi import APIRouter

from app.api.routes import documents, glossary

api_router = APIRouter(prefix="/api")
api_router.include_router(documents.router)
api_router.include_router(glossary.router)
```

- [ ] **Step 7: Run parser tests**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_pdf_parser.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add backend/app/schemas/documents.py backend/app/services/pdf_parser.py backend/app/services/documents.py backend/app/api/routes/documents.py backend/app/api/router.py backend/tests/test_pdf_parser.py
git commit -m "feat: parse uploaded pdfs"
```

---

## Task 5: Prompt Construction And Translation State Service

**Files:**
- Create: `backend/app/services/prompts.py`
- Create: `backend/app/services/ai_client.py`
- Create: `backend/app/services/translations.py`
- Create: `backend/app/schemas/translations.py`
- Create: `backend/app/api/routes/translations.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_prompts.py`

- [ ] **Step 1: Write failing prompt test**

Create `backend/tests/test_prompts.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_prompts.py -v
```

Expected: FAIL because `app.services.prompts` does not exist.

- [ ] **Step 3: Implement prompt builder**

Create `backend/app/services/prompts.py`:

```python
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
```

- [ ] **Step 4: Implement AI client**

Create `backend/app/services/ai_client.py`:

```python
import httpx

from app.core.config import settings


class AIClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self.api_key = api_key if api_key is not None else settings.api_key
        self.base_url = (base_url if base_url is not None else settings.base_url).rstrip("/")
        self.model = model if model is not None else settings.model_name

    async def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("API key is not configured")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a precise academic translation assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
```

- [ ] **Step 5: Implement translation service**

Create `backend/app/services/translations.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Paragraph, ParagraphStatus, TranslationJob
from app.services.ai_client import AIClient
from app.services.glossary import list_enabled_terms
from app.services.prompts import GlossaryPromptTerm, build_translation_prompt


def glossary_for_prompt(db: Session) -> list[GlossaryPromptTerm]:
    return [
        GlossaryPromptTerm(
            source_term=term.source_term,
            target_term=term.target_term,
            keep_english=term.keep_english,
        )
        for term in list_enabled_terms(db)
    ]


async def translate_paragraph(db: Session, paragraph_id: int, ai_client: AIClient | None = None) -> Paragraph:
    paragraph = db.get(Paragraph, paragraph_id)
    if paragraph is None:
        raise ValueError("Paragraph not found")

    paragraph.status = ParagraphStatus.translating
    db.commit()
    db.refresh(paragraph)

    client = ai_client or AIClient()
    prompt = build_translation_prompt(
        source_text=paragraph.source_text,
        context_before="",
        context_after="",
        glossary=glossary_for_prompt(db),
    )

    try:
        paragraph.translated_text = await client.complete(prompt)
        paragraph.status = ParagraphStatus.translated
    except Exception:
        paragraph.status = ParagraphStatus.failed
        db.commit()
        raise

    db.commit()
    db.refresh(paragraph)
    return paragraph


def create_document_translation_job(db: Session, document_id: int) -> TranslationJob:
    paragraphs = list(
        db.scalars(
            select(Paragraph)
            .where(Paragraph.document_id == document_id)
            .where(Paragraph.status.in_([ParagraphStatus.pending, ParagraphStatus.failed]))
            .order_by(Paragraph.page_number, Paragraph.order_index)
        )
    )
    job = TranslationJob(document_id=document_id, status="queued", total_count=len(paragraphs))
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


async def run_document_translation(db: Session, job_id: int, initial_pages: int = 3) -> TranslationJob:
    job = db.get(TranslationJob, job_id)
    if job is None:
        raise ValueError("Translation job not found")

    job.status = "running"
    db.commit()

    priority_paragraphs = list(
        db.scalars(
            select(Paragraph)
            .where(Paragraph.document_id == job.document_id)
            .where(Paragraph.page_number <= initial_pages)
            .where(Paragraph.status.in_([ParagraphStatus.pending, ParagraphStatus.failed]))
            .order_by(Paragraph.page_number, Paragraph.order_index)
        )
    )
    remaining_paragraphs = list(
        db.scalars(
            select(Paragraph)
            .where(Paragraph.document_id == job.document_id)
            .where(Paragraph.page_number > initial_pages)
            .where(Paragraph.status.in_([ParagraphStatus.pending, ParagraphStatus.failed]))
            .order_by(Paragraph.page_number, Paragraph.order_index)
        )
    )

    for paragraph in [*priority_paragraphs, *remaining_paragraphs]:
        try:
            await translate_paragraph(db, paragraph.id)
            job.completed_count += 1
        except Exception:
            job.failed_count += 1
        db.commit()

    job.status = "completed" if job.failed_count == 0 else "completed_with_errors"
    db.commit()
    db.refresh(job)
    return job
```

- [ ] **Step 6: Add translation route**

Create `backend/app/schemas/translations.py`:

```python
from pydantic import BaseModel


class TranslateParagraphRequest(BaseModel):
    paragraph_id: int


class TranslateParagraphResponse(BaseModel):
    paragraph_id: int
    translated_text: str
    status: str


class StartDocumentTranslationResponse(BaseModel):
    job_id: int
    status: str
    total_count: int
```

Create `backend/app/api/routes/translations.py`:

```python
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.session import SessionLocal
from app.schemas.translations import StartDocumentTranslationResponse, TranslateParagraphRequest, TranslateParagraphResponse
from app.services.translations import create_document_translation_job, run_document_translation, translate_paragraph

router = APIRouter(prefix="/translations", tags=["translations"])


@router.post("/paragraph", response_model=TranslateParagraphResponse)
async def post_translate_paragraph(payload: TranslateParagraphRequest, db: Session = Depends(get_db)):
    try:
        paragraph = await translate_paragraph(db, payload.paragraph_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TranslateParagraphResponse(
        paragraph_id=paragraph.id,
        translated_text=paragraph.translated_text,
        status=paragraph.status.value,
    )


async def run_job_in_new_session(job_id: int) -> None:
    db = SessionLocal()
    try:
        await run_document_translation(db, job_id)
    finally:
        db.close()


@router.post("/documents/{document_id}/start", response_model=StartDocumentTranslationResponse)
def start_document_translation(document_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job = create_document_translation_job(db, document_id)
    background_tasks.add_task(run_job_in_new_session, job.id)
    return StartDocumentTranslationResponse(job_id=job.id, status=job.status, total_count=job.total_count)
```

Modify `backend/app/api/router.py`:

```python
from fastapi import APIRouter

from app.api.routes import documents, glossary, translations

api_router = APIRouter(prefix="/api")
api_router.include_router(documents.router)
api_router.include_router(glossary.router)
api_router.include_router(translations.router)
```

- [ ] **Step 7: Run prompt tests**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_prompts.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add backend/app/services/prompts.py backend/app/services/ai_client.py backend/app/services/translations.py backend/app/schemas/translations.py backend/app/api/routes/translations.py backend/app/api/router.py backend/tests/test_prompts.py
git commit -m "feat: add translation prompts"
```

---

## Task 6: Settings, Correction, And Assistant APIs

**Files:**
- Create: `backend/app/schemas/settings.py`
- Create: `backend/app/services/settings.py`
- Create: `backend/app/api/routes/settings.py`
- Create: `backend/app/schemas/corrections.py`
- Create: `backend/app/services/corrections.py`
- Create: `backend/app/api/routes/corrections.py`
- Create: `backend/app/schemas/assistant.py`
- Create: `backend/app/api/routes/assistant.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/tests/test_settings_api.py`

- [ ] **Step 1: Write failing settings service test**

Create `backend/tests/test_settings_api.py`:

```python
from app.core.config import Settings
from app.services.settings import public_settings


def test_public_settings_masks_api_key():
    settings = Settings(api_key="sk-1234567890abcdef", base_url="https://example.com/v1", model_name="test-model")

    result = public_settings(settings)

    assert result["api_key_masked"] == "sk-********cdef"
    assert result["base_url"] == "https://example.com/v1"
    assert result["model_name"] == "test-model"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_settings_api.py -v
```

Expected: FAIL because `app.services.settings` does not exist.

- [ ] **Step 3: Implement settings service and route**

Create `backend/app/services/settings.py`:

```python
from app.core.config import Settings, settings


def public_settings(current: Settings = settings) -> dict[str, str | int]:
    return {
        "api_key_masked": current.masked_api_key,
        "base_url": current.base_url,
        "model_name": current.model_name,
        "mysql_host": current.mysql_host,
        "mysql_port": current.mysql_port,
        "mysql_database": current.mysql_database,
        "storage_dir": current.storage_dir,
        "translation_concurrency": current.translation_concurrency,
        "translation_batch_size": current.translation_batch_size,
    }
```

Create `backend/app/schemas/settings.py`:

```python
from pydantic import BaseModel


class PublicSettings(BaseModel):
    api_key_masked: str
    base_url: str
    model_name: str
    mysql_host: str
    mysql_port: int
    mysql_database: str
    storage_dir: str
    translation_concurrency: int
    translation_batch_size: int
```

Create `backend/app/api/routes/settings.py`:

```python
from fastapi import APIRouter

from app.schemas.settings import PublicSettings
from app.services.settings import public_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=PublicSettings)
def get_settings():
    return public_settings()
```

- [ ] **Step 4: Implement correction service and route**

Create `backend/app/schemas/corrections.py`:

```python
from pydantic import BaseModel


class ReplaceTranslationRequest(BaseModel):
    paragraph_id: int
    new_text: str


class ReplaceTranslationResponse(BaseModel):
    paragraph_id: int
    translated_text: str
    status: str
```

Create `backend/app/services/corrections.py`:

```python
from sqlalchemy.orm import Session

from app.db.models import Correction, Paragraph, ParagraphStatus


def replace_translation(db: Session, paragraph_id: int, new_text: str) -> Paragraph:
    paragraph = db.get(Paragraph, paragraph_id)
    if paragraph is None:
        raise ValueError("Paragraph not found")
    db.add(Correction(paragraph_id=paragraph.id, old_text=paragraph.translated_text, new_text=new_text))
    paragraph.translated_text = new_text
    paragraph.status = ParagraphStatus.corrected
    db.commit()
    db.refresh(paragraph)
    return paragraph
```

Create `backend/app/api/routes/corrections.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.corrections import ReplaceTranslationRequest, ReplaceTranslationResponse
from app.services.corrections import replace_translation

router = APIRouter(prefix="/corrections", tags=["corrections"])


@router.post("/replace", response_model=ReplaceTranslationResponse)
def post_replace_translation(payload: ReplaceTranslationRequest, db: Session = Depends(get_db)):
    try:
        paragraph = replace_translation(db, payload.paragraph_id, payload.new_text)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReplaceTranslationResponse(
        paragraph_id=paragraph.id,
        translated_text=paragraph.translated_text,
        status=paragraph.status.value,
    )
```

- [ ] **Step 5: Implement assistant route**

Create `backend/app/schemas/assistant.py`:

```python
from pydantic import BaseModel


class AskAssistantRequest(BaseModel):
    question: str
    selected_text: str
    source_text: str = ""


class AskAssistantResponse(BaseModel):
    answer: str
```

Create `backend/app/api/routes/assistant.py`:

```python
from fastapi import APIRouter

from app.schemas.assistant import AskAssistantRequest, AskAssistantResponse
from app.services.ai_client import AIClient

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=AskAssistantResponse)
async def post_ask_assistant(payload: AskAssistantRequest):
    prompt = (
        "Answer the user's question in Simplified Chinese using the selected academic text.\n"
        f"Question: {payload.question}\n"
        f"Selected Chinese text: {payload.selected_text}\n"
        f"Original source text: {payload.source_text or 'Not provided'}"
    )
    answer = await AIClient().complete(prompt)
    return AskAssistantResponse(answer=answer)
```

- [ ] **Step 6: Register routes**

Modify `backend/app/api/router.py`:

```python
from fastapi import APIRouter

from app.api.routes import assistant, corrections, documents, glossary, settings, translations

api_router = APIRouter(prefix="/api")
api_router.include_router(assistant.router)
api_router.include_router(corrections.router)
api_router.include_router(documents.router)
api_router.include_router(glossary.router)
api_router.include_router(settings.router)
api_router.include_router(translations.router)
```

- [ ] **Step 7: Run tests**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest tests/test_settings_api.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add backend/app/schemas/settings.py backend/app/services/settings.py backend/app/api/routes/settings.py backend/app/schemas/corrections.py backend/app/services/corrections.py backend/app/api/routes/corrections.py backend/app/schemas/assistant.py backend/app/api/routes/assistant.py backend/app/api/router.py backend/tests/test_settings_api.py
git commit -m "feat: add settings and correction apis"
```

---

## Task 7: Frontend Scaffold, Routing, And API Client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/components/AppShell.vue`
- Create: `frontend/src/components/StatusBadge.vue`

- [ ] **Step 1: Add frontend package metadata**

Create `frontend/package.json`:

```json
{
  "name": "easypdf-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5173",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-vue": "^5.0.5",
    "pdfjs-dist": "^4.4.168",
    "pinia": "^2.1.7",
    "vue": "^3.4.29",
    "vue-router": "^4.3.3"
  },
  "devDependencies": {
    "typescript": "^5.4.5",
    "vite": "^5.3.1",
    "vitest": "^1.6.0",
    "vue-tsc": "^2.0.22"
  }
}
```

- [ ] **Step 2: Add Vite and TypeScript files**

Create `frontend/index.html`:

```html
<div id="app"></div>
<script type="module" src="/src/main.ts"></script>
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "preserve",
    "sourceMap": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "lib": ["ES2022", "DOM"]
  },
  "include": ["src/**/*.ts", "src/**/*.vue", "tests/**/*.ts"]
}
```

Create `frontend/vite.config.ts`:

```ts
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000"
    }
  }
});
```

- [ ] **Step 3: Add shared types and API client**

Create `frontend/src/types.ts`:

```ts
export type ParagraphStatus = "pending" | "translating" | "translated" | "failed" | "corrected";

export interface DocumentSummary {
  id: number;
  title: string;
  original_filename: string;
  status: string;
}

export interface Paragraph {
  id: number;
  page_number: number;
  order_index: number;
  source_text: string;
  translated_text: string;
  status: ParagraphStatus;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface DocumentDetail extends DocumentSummary {
  paragraphs: Paragraph[];
}

export interface GlossaryTerm {
  id: number;
  source_term: string;
  target_term: string;
  note: string;
  enabled: boolean;
  keep_english: boolean;
}
```

Create `frontend/src/api/client.ts`:

```ts
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}
```

- [ ] **Step 4: Add app shell**

Create `frontend/src/components/AppShell.vue`:

```vue
<template>
  <div class="app-shell">
    <aside>
      <div class="brand">EasyPDF</div>
      <RouterLink to="/">文档库</RouterLink>
      <RouterLink to="/glossary">术语表</RouterLink>
      <RouterLink to="/settings">设置</RouterLink>
    </aside>
    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 220px 1fr;
  background: #f5f3ee;
  color: #20231f;
}
aside {
  border-right: 1px solid #d8d3c8;
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #fbfaf7;
}
.brand {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 18px;
}
a {
  color: #2f4f4f;
  padding: 10px 12px;
  border-radius: 6px;
  text-decoration: none;
}
a.router-link-active {
  background: #e4ebe7;
}
main {
  min-width: 0;
}
</style>
```

Create `frontend/src/components/StatusBadge.vue`:

```vue
<script setup lang="ts">
defineProps<{ status: string }>();
</script>

<template>
  <span class="badge" :data-status="status">{{ status }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  border-radius: 4px;
  background: #e9e4da;
  color: #4a453d;
  font-size: 12px;
}
.badge[data-status="failed"] {
  background: #f2d7d5;
  color: #8a3028;
}
.badge[data-status="translated"],
.badge[data-status="corrected"] {
  background: #dce9e1;
  color: #28533c;
}
</style>
```

- [ ] **Step 5: Add router and app entry**

Create `frontend/src/router.ts`:

```ts
import { createRouter, createWebHistory } from "vue-router";

const DocumentLibrary = () => import("./views/DocumentLibrary.vue");
const ReaderView = () => import("./views/ReaderView.vue");
const SettingsView = () => import("./views/SettingsView.vue");
const GlossaryView = () => import("./views/GlossaryView.vue");

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: DocumentLibrary },
    { path: "/documents/:id", component: ReaderView },
    { path: "/settings", component: SettingsView },
    { path: "/glossary", component: GlossaryView }
  ]
});
```

Create `frontend/src/App.vue`:

```vue
<template>
  <AppShell />
</template>

<script setup lang="ts">
import AppShell from "./components/AppShell.vue";
</script>
```

Create `frontend/src/main.ts`:

```ts
import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import "./styles.css";

createApp(App).use(createPinia()).use(router).mount("#app");
```

Create `frontend/src/styles.css`:

```css
* {
  box-sizing: border-box;
}
body {
  margin: 0;
  font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
}
button,
input,
textarea {
  font: inherit;
}
```

- [ ] **Step 6: Install dependencies and build**

Run:

```powershell
cd D:\Project\EasyPDF\frontend
npm install
npm run build
```

Expected: dependency install succeeds and Vite build completes.

- [ ] **Step 7: Commit**

```powershell
git add frontend
git commit -m "feat: scaffold vue frontend"
```

---

## Task 8: Document Library, Settings, And Glossary Screens

**Files:**
- Create: `frontend/src/views/DocumentLibrary.vue`
- Create: `frontend/src/views/SettingsView.vue`
- Create: `frontend/src/views/GlossaryView.vue`

- [ ] **Step 1: Add document library**

Create `frontend/src/views/DocumentLibrary.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { apiGet } from "../api/client";
import StatusBadge from "../components/StatusBadge.vue";
import type { DocumentSummary } from "../types";

const router = useRouter();
const documents = ref<DocumentSummary[]>([]);
const error = ref("");

async function loadDocuments() {
  try {
    documents.value = await apiGet<DocumentSummary[]>("/api/documents");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载文档失败";
  }
}

onMounted(loadDocuments);
</script>

<template>
  <section class="page">
    <header>
      <h1>文档库</h1>
      <label class="upload">
        上传 PDF
        <input type="file" accept="application/pdf" hidden />
      </label>
    </header>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="documents">
      <button v-for="doc in documents" :key="doc.id" class="document-row" @click="router.push(`/documents/${doc.id}`)">
        <span>{{ doc.title }}</span>
        <StatusBadge :status="doc.status" />
      </button>
    </div>
  </section>
</template>

<style scoped>
.page {
  padding: 28px;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
h1 {
  margin: 0;
  font-size: 28px;
}
.upload {
  background: #2f4f4f;
  color: white;
  padding: 10px 14px;
  border-radius: 6px;
}
.documents {
  margin-top: 22px;
  display: grid;
  gap: 10px;
}
.document-row {
  border: 1px solid #d8d3c8;
  background: white;
  border-radius: 6px;
  padding: 14px;
  display: flex;
  justify-content: space-between;
  text-align: left;
  cursor: pointer;
}
.error {
  color: #8a3028;
}
</style>
```

- [ ] **Step 2: Add settings screen**

Create `frontend/src/views/SettingsView.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";

import { apiGet } from "../api/client";

interface PublicSettings {
  api_key_masked: string;
  base_url: string;
  model_name: string;
  mysql_host: string;
  mysql_port: number;
  mysql_database: string;
  storage_dir: string;
  translation_concurrency: number;
  translation_batch_size: number;
}

const settings = ref<PublicSettings | null>(null);

onMounted(async () => {
  settings.value = await apiGet<PublicSettings>("/api/settings");
});
</script>

<template>
  <section class="page">
    <h1>设置</h1>
    <div v-if="settings" class="grid">
      <label>API_KEY<input :value="settings.api_key_masked" disabled /></label>
      <label>BASE_URL<input :value="settings.base_url" disabled /></label>
      <label>模型<input :value="settings.model_name" disabled /></label>
      <label>MySQL<input :value="`${settings.mysql_host}:${settings.mysql_port}/${settings.mysql_database}`" disabled /></label>
      <label>存储目录<input :value="settings.storage_dir" disabled /></label>
      <label>翻译并发<input :value="settings.translation_concurrency" disabled /></label>
    </div>
  </section>
</template>

<style scoped>
.page {
  padding: 28px;
}
.grid {
  max-width: 760px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
label {
  display: grid;
  gap: 6px;
  color: #4f4a42;
}
input {
  height: 38px;
  border: 1px solid #d8d3c8;
  border-radius: 6px;
  padding: 0 10px;
  background: white;
}
</style>
```

- [ ] **Step 3: Add glossary screen**

Create `frontend/src/views/GlossaryView.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";

import { apiGet, apiPost } from "../api/client";
import type { GlossaryTerm } from "../types";

const terms = ref<GlossaryTerm[]>([]);
const source = ref("");
const target = ref("");

async function loadTerms() {
  terms.value = await apiGet<GlossaryTerm[]>("/api/glossary");
}

async function addTerm() {
  await apiPost<GlossaryTerm>("/api/glossary", {
    source_term: source.value,
    target_term: target.value,
    note: "",
    keep_english: false
  });
  source.value = "";
  target.value = "";
  await loadTerms();
}

onMounted(loadTerms);
</script>

<template>
  <section class="page">
    <h1>术语表</h1>
    <form class="term-form" @submit.prevent="addTerm">
      <input v-model="source" aria-label="英文术语" />
      <input v-model="target" aria-label="中文译法" />
      <button>添加</button>
    </form>
    <div class="terms">
      <div v-for="term in terms" :key="term.id" class="term-row">
        <strong>{{ term.source_term }}</strong>
        <span>{{ term.target_term }}</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.page {
  padding: 28px;
}
.term-form {
  display: grid;
  grid-template-columns: 1fr 1fr 96px;
  gap: 10px;
  max-width: 820px;
}
input,
button {
  height: 38px;
  border-radius: 6px;
  border: 1px solid #d8d3c8;
  padding: 0 10px;
}
button {
  background: #2f4f4f;
  color: white;
}
.terms {
  margin-top: 20px;
  display: grid;
  gap: 8px;
}
.term-row {
  max-width: 820px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  border: 1px solid #d8d3c8;
  background: white;
  border-radius: 6px;
  padding: 12px;
}
</style>
```

- [ ] **Step 4: Build frontend**

Run:

```powershell
cd D:\Project\EasyPDF\frontend
npm run build
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/views/DocumentLibrary.vue frontend/src/views/SettingsView.vue frontend/src/views/GlossaryView.vue
git commit -m "feat: add library settings and glossary views"
```

---

## Task 9: Reader View, PDF.js Pane, Selection Toolbar, And Correction Panel

**Files:**
- Create: `frontend/src/components/PdfPane.vue`
- Create: `frontend/src/components/SelectionToolbar.vue`
- Create: `frontend/src/views/ReaderView.vue`
- Create: `frontend/tests/reader-selection.test.ts`

- [ ] **Step 1: Write failing selection helper test**

Create `frontend/tests/reader-selection.test.ts`:

```ts
import { describe, expect, it } from "vitest";

function shouldShowToolbar(selectedText: string): boolean {
  return selectedText.trim().length > 0;
}

describe("reader selection", () => {
  it("shows toolbar only when selected text is not empty", () => {
    expect(shouldShowToolbar("  ")).toBe(false);
    expect(shouldShowToolbar("translated paragraph")).toBe(true);
  });
});
```

- [ ] **Step 2: Run frontend test**

Run:

```powershell
cd D:\Project\EasyPDF\frontend
npm test
```

Expected: PASS. This locks the selection rule before wiring the UI.

- [ ] **Step 3: Add selection toolbar component**

Create `frontend/src/components/SelectionToolbar.vue`:

```vue
<script setup lang="ts">
defineEmits<{
  showOriginal: [];
  retranslate: [];
  askAi: [];
}>();
</script>

<template>
  <div class="toolbar">
    <button @click="$emit('showOriginal')">查看原文</button>
    <button @click="$emit('retranslate')">重新翻译</button>
    <button @click="$emit('askAi')">问 AI</button>
  </div>
</template>

<style scoped>
.toolbar {
  position: sticky;
  top: 12px;
  z-index: 2;
  display: flex;
  gap: 8px;
  padding: 8px;
  background: #fffdf8;
  border: 1px solid #d8d3c8;
  border-radius: 6px;
  box-shadow: 0 10px 28px rgb(32 35 31 / 12%);
}
button {
  border: 0;
  border-radius: 4px;
  background: #2f4f4f;
  color: white;
  padding: 8px 10px;
}
</style>
```

- [ ] **Step 4: Add PDF.js pane component**

Create `frontend/src/components/PdfPane.vue`:

```vue
<script setup lang="ts">
import * as pdfjsLib from "pdfjs-dist";
import workerUrl from "pdfjs-dist/build/pdf.worker.mjs?url";
import { onMounted, ref, watch } from "vue";

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl;

const props = defineProps<{ fileUrl: string }>();
const canvas = ref<HTMLCanvasElement | null>(null);
const pageNumber = ref(1);

async function renderPage() {
  if (!canvas.value || !props.fileUrl) return;
  const loadingTask = pdfjsLib.getDocument(props.fileUrl);
  const pdf = await loadingTask.promise;
  const page = await pdf.getPage(pageNumber.value);
  const viewport = page.getViewport({ scale: 1.25 });
  const context = canvas.value.getContext("2d");
  if (!context) return;
  canvas.value.width = viewport.width;
  canvas.value.height = viewport.height;
  await page.render({ canvasContext: context, viewport }).promise;
}

onMounted(renderPage);
watch(() => props.fileUrl, renderPage);
</script>

<template>
  <div class="pdf-pane-inner">
    <canvas ref="canvas" />
  </div>
</template>

<style scoped>
.pdf-pane-inner {
  display: grid;
  justify-items: center;
}
canvas {
  max-width: 100%;
  background: white;
  box-shadow: 0 14px 34px rgb(32 35 31 / 18%);
}
</style>
```

- [ ] **Step 5: Add reader view**

Create `frontend/src/views/ReaderView.vue`:

```vue
<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiGet, apiPost } from "../api/client";
import PdfPane from "../components/PdfPane.vue";
import SelectionToolbar from "../components/SelectionToolbar.vue";
import StatusBadge from "../components/StatusBadge.vue";
import type { DocumentDetail, Paragraph } from "../types";

const route = useRoute();
const documentDetail = ref<DocumentDetail | null>(null);
const selectedParagraph = ref<Paragraph | null>(null);
const selectedText = ref("");
const panelMode = ref<"none" | "source" | "ai">("none");
const aiQuestion = ref("");
const aiAnswer = ref("");

const pdfUrl = computed(() => `/api/documents/${route.params.id}/file`);
const paragraphs = computed(() => documentDetail.value?.paragraphs ?? []);

async function loadDocument() {
  documentDetail.value = await apiGet<DocumentDetail>(`/api/documents/${route.params.id}`);
}

function selectParagraph(paragraph: Paragraph) {
  selectedParagraph.value = paragraph;
  selectedText.value = paragraph.translated_text || paragraph.source_text;
  panelMode.value = "none";
}

function showOriginal() {
  panelMode.value = "source";
}

async function retranslate() {
  if (!selectedParagraph.value) return;
  const result = await apiPost<{ translated_text: string; status: string }>("/api/translations/paragraph", {
    paragraph_id: selectedParagraph.value.id
  });
  selectedParagraph.value.translated_text = result.translated_text;
  selectedParagraph.value.status = result.status as Paragraph["status"];
}

async function askAi() {
  if (!selectedParagraph.value) return;
  panelMode.value = "ai";
  const result = await apiPost<{ answer: string }>("/api/assistant/ask", {
    question: aiQuestion.value || "请解释这段内容的核心含义。",
    selected_text: selectedText.value,
    source_text: selectedParagraph.value.source_text
  });
  aiAnswer.value = result.answer;
}

onMounted(loadDocument);
</script>

<template>
  <section class="reader">
    <header>
      <h1>{{ documentDetail?.title || "阅读器" }}</h1>
      <span>{{ paragraphs.length }} 段</span>
    </header>
    <div class="panes">
      <aside class="pdf-pane">
        <PdfPane :file-url="pdfUrl" />
      </aside>
      <main class="translation-pane">
        <SelectionToolbar
          v-if="selectedParagraph"
          @show-original="showOriginal"
          @retranslate="retranslate"
          @ask-ai="askAi"
        />
        <article
          v-for="paragraph in paragraphs"
          :key="paragraph.id"
          class="paragraph"
          :class="{ selected: selectedParagraph?.id === paragraph.id }"
          @mouseup="selectParagraph(paragraph)"
          @touchend="selectParagraph(paragraph)"
        >
          <div class="paragraph-meta">
            <span>第 {{ paragraph.page_number }} 页</span>
            <StatusBadge :status="paragraph.status" />
          </div>
          <p>{{ paragraph.translated_text || paragraph.source_text }}</p>
        </article>
      </main>
      <aside class="side-panel">
        <template v-if="selectedParagraph && panelMode === 'source'">
          <h2>原文</h2>
          <p>{{ selectedParagraph.source_text }}</p>
        </template>
        <template v-else-if="selectedParagraph && panelMode === 'ai'">
          <h2>AI 助手</h2>
          <textarea v-model="aiQuestion" aria-label="输入你的问题"></textarea>
          <button @click="askAi">提问</button>
          <p>{{ aiAnswer }}</p>
        </template>
        <p v-else>选中右侧段落后可查看原文、重译或提问。</p>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.reader {
  height: 100vh;
  display: grid;
  grid-template-rows: 64px 1fr;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid #d8d3c8;
  background: #fbfaf7;
}
h1 {
  font-size: 20px;
  margin: 0;
}
.panes {
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(360px, 42%) minmax(420px, 1fr) 320px;
}
.pdf-pane,
.translation-pane,
.side-panel {
  min-height: 0;
  overflow: auto;
  border-right: 1px solid #d8d3c8;
}
.pdf-pane {
  background: #e9e6de;
  padding: 18px;
}
.translation-pane {
  padding: 18px;
  background: #fffdf8;
}
.paragraph {
  border: 1px solid transparent;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  background: white;
}
.paragraph.selected {
  border-color: #52796f;
  background: #f2f7f4;
}
.paragraph-meta {
  display: flex;
  justify-content: space-between;
  color: #6a6258;
  font-size: 12px;
}
.side-panel {
  background: #fbfaf7;
  padding: 18px;
}
textarea {
  width: 100%;
  min-height: 88px;
  resize: vertical;
}
</style>
```

- [ ] **Step 6: Run frontend tests and build**

Run:

```powershell
cd D:\Project\EasyPDF\frontend
npm test
npm run build
```

Expected: Vitest and build both PASS.

- [ ] **Step 7: Commit**

```powershell
git add frontend/src/components/PdfPane.vue frontend/src/components/SelectionToolbar.vue frontend/src/views/ReaderView.vue frontend/tests/reader-selection.test.ts
git commit -m "feat: add reader correction workflow"
```

---

## Task 10: Development Scripts And End-To-End Smoke Check

**Files:**
- Create: `scripts/dev.ps1`
- Modify: `README.md`

- [ ] **Step 1: Add development script**

Create `scripts/dev.ps1`:

```powershell
$ErrorActionPreference = "Stop"

Write-Host "Starting EasyPDF backend on http://127.0.0.1:8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "conda activate lang_chain01; cd D:\Project\EasyPDF\backend; uvicorn app.main:app --reload --port 8000"

Write-Host "Starting EasyPDF frontend on http://127.0.0.1:5173"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\Project\EasyPDF\frontend; npm run dev"
```

- [ ] **Step 2: Add README**

Create `README.md`:

```markdown
# EasyPDF

EasyPDF is a local-first web app for reading English academic PDFs in Chinese with side-by-side original PDF and translated paragraph views.

## Local Setup

1. Create MySQL database:

   ```powershell
   mysql -uroot -p123456 < scripts/init-db.sql
   ```

2. Configure backend:

   ```powershell
   cd backend
   Copy-Item .env.example .env
   ```

   Fill `MYSQL_PASSWORD`, `API_KEY`, `BASE_URL`, and `MODEL_NAME` in `backend/.env`.

3. Run migrations:

   ```powershell
   conda activate lang_chain01
   cd backend
   alembic upgrade head
   ```

4. Install and build frontend:

   ```powershell
   cd ..\frontend
   npm install
   npm run build
   ```

5. Start both services:

   ```powershell
   cd ..
   .\scripts\dev.ps1
   ```

Open `http://127.0.0.1:5173`.
```

- [ ] **Step 3: Run full backend tests**

Run:

```powershell
cd D:\Project\EasyPDF\backend
pytest -v
```

Expected: all backend tests PASS.

- [ ] **Step 4: Run full frontend checks**

Run:

```powershell
cd D:\Project\EasyPDF\frontend
npm test
npm run build
```

Expected: Vitest and Vite build PASS.

- [ ] **Step 5: Run local smoke check**

Run:

```powershell
cd D:\Project\EasyPDF
.\scripts\dev.ps1
```

Expected:

- Backend responds at `http://127.0.0.1:8000/health`.
- Frontend opens at `http://127.0.0.1:5173`.
- Document library renders.
- Settings page renders masked API configuration.
- Glossary page can add and reload a term.

- [ ] **Step 6: Commit**

```powershell
git add scripts/dev.ps1 README.md
git commit -m "docs: add local development workflow"
```

---

## Final Verification

- [ ] Run backend tests:

```powershell
cd D:\Project\EasyPDF\backend
pytest -v
```

Expected: all tests PASS.

- [ ] Run frontend tests and build:

```powershell
cd D:\Project\EasyPDF\frontend
npm test
npm run build
```

Expected: all checks PASS.

- [ ] Check Git status:

```powershell
cd D:\Project\EasyPDF
git status -sb
```

Expected: clean working tree on the implementation branch.

- [ ] Push:

```powershell
git push
```

Expected: branch updates on `git@github.com:cjlwuhu/EasyPDF.git`.

---

## Spec Coverage Review

- Local single-user FastAPI/Vue/MySQL app: Tasks 1, 2, 7, 10.
- Text-based PDF upload and parsing: Task 4.
- Original PDF display surface and Chinese paragraph stream: Task 4 exposes the original PDF file and Task 9 renders it with PDF.js beside translated paragraphs.
- Paragraph-level mapping: Tasks 2 and 4.
- Hybrid translation workflow foundation: Task 5 establishes paragraph-level translation state, creates document translation jobs, prioritizes initial pages, and runs remaining paragraphs through FastAPI background tasks.
- API configuration and model settings: Tasks 1 and 6.
- Retranslation and manual replacement: Tasks 5 and 6.
- AI question panel: Tasks 6 and 9.
- Local MySQL persistence: Task 2.
- Glossary: Tasks 3 and 8.
- OCR, multi-user login, cloud sync, exact translated PDF layout, advanced formula recognition, billing, and desktop packaging remain outside this MVP plan.
