from pathlib import Path

import fitz

from app.services.pdf_parser import ParsedBlock, order_text_blocks, parse_pdf


def block(text: str, x0: float, y0: float, x1: float, y1: float) -> ParsedBlock:
    return ParsedBlock(
        page_number=1,
        order_index=0,
        x0=x0,
        y0=y0,
        x1=x1,
        y1=y1,
        text=text,
    )


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


def test_single_column_order_falls_back_to_top_then_left():
    blocks = [
        block("bottom", 40, 160, 560, 195),
        block("top", 40, 80, 560, 115),
    ]

    assert [item.text for item in order_text_blocks(blocks, page_width=600)] == ["top", "bottom"]


def test_two_column_order_reads_left_column_before_right():
    blocks = [
        block("right top", 330, 80, 560, 120),
        block("left bottom", 40, 180, 270, 220),
        block("left top", 40, 80, 270, 120),
        block("right bottom", 330, 180, 560, 220),
    ]

    assert [item.text for item in order_text_blocks(blocks, page_width=600)] == [
        "left top",
        "left bottom",
        "right top",
        "right bottom",
    ]


def test_two_column_order_handles_a_column_returned_as_one_block():
    blocks = [
        block("right column body", 330, 80, 560, 500),
        block("left heading", 40, 80, 270, 120),
        block("left column body", 40, 140, 270, 500),
    ]

    assert [item.text for item in order_text_blocks(blocks, page_width=600)] == [
        "left heading",
        "left column body",
        "right column body",
    ]


def test_spanning_block_splits_two_column_bands():
    blocks = [
        block("title", 40, 20, 560, 55),
        block("left", 40, 80, 270, 120),
        block("right", 330, 80, 560, 120),
        block("figure caption", 70, 160, 530, 190),
        block("left after", 40, 220, 270, 250),
        block("right after", 330, 220, 560, 250),
    ]

    assert [item.text for item in order_text_blocks(blocks, page_width=600)] == [
        "title",
        "left",
        "right",
        "figure caption",
        "left after",
        "right after",
    ]
