from __future__ import annotations

import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    pages: Mapped[list[Page]] = relationship(back_populates="document", cascade="all, delete-orphan")
    paragraphs: Mapped[list[Paragraph]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("document_id", "page_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    width: Mapped[float] = mapped_column(Float, default=0)
    height: Mapped[float] = mapped_column(Float, default=0)

    document: Mapped[Document] = relationship(back_populates="pages")
    blocks: Mapped[list[Block]] = relationship(back_populates="page", cascade="all, delete-orphan")


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    block_type: Mapped[BlockType] = mapped_column(Enum(BlockType))
    order_index: Mapped[int] = mapped_column(Integer)
    x0: Mapped[float] = mapped_column(Float, default=0)
    y0: Mapped[float] = mapped_column(Float, default=0)
    x1: Mapped[float] = mapped_column(Float, default=0)
    y1: Mapped[float] = mapped_column(Float, default=0)
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
    x0: Mapped[float] = mapped_column(Float, default=0)
    y0: Mapped[float] = mapped_column(Float, default=0)
    x1: Mapped[float] = mapped_column(Float, default=0)
    y1: Mapped[float] = mapped_column(Float, default=0)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class TranslationJob(Base):
    __tablename__ = "translation_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(64), default="queued")
    total_count: Mapped[int] = mapped_column(default=0)
    completed_count: Mapped[int] = mapped_column(default=0)
    failed_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class ReaderPosition(Base):
    __tablename__ = "reader_positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    page_number: Mapped[int] = mapped_column(default=1)
    paragraph_id: Mapped[int | None] = mapped_column(ForeignKey("paragraphs.id", ondelete="SET NULL"), nullable=True)
    scroll_top: Mapped[int] = mapped_column(default=0)
