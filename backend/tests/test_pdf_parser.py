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
