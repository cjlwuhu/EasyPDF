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
