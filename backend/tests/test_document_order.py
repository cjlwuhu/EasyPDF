from app.db.models import Document, Page, Paragraph
from app.services.documents import order_document_paragraphs


def paragraph(text: str, order_index: int, x0: float, y0: float, x1: float, y1: float) -> Paragraph:
    return Paragraph(
        page_number=1,
        order_index=order_index,
        source_text=text,
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
    )


def test_orders_legacy_document_paragraphs_by_columns():
    document = Document(title="Paper", original_filename="paper.pdf", file_path="paper.pdf")
    document.pages.append(Page(page_number=1, width=600, height=800))
    document.paragraphs.extend(
        [
            paragraph("right column", 0, 330, 80, 560, 500),
            paragraph("left bottom", 1, 40, 140, 270, 500),
            paragraph("left top", 2, 40, 80, 270, 120),
        ]
    )

    assert [item.source_text for item in order_document_paragraphs(document)] == [
        "left top",
        "left bottom",
        "right column",
    ]
