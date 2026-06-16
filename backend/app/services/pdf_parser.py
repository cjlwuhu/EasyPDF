from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

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
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


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
    return re.sub(r"\s+", " ", text).strip()


def parse_pdf(path: str | Path) -> ParsedPdf:
    pages: list[ParsedPage] = []
    blocks: list[ParsedBlock] = []
    paragraphs: list[ParsedParagraph] = []

    with fitz.open(path) as document:
        paragraph_index = 0
        for page_index, page in enumerate(document, start=1):
            rect = page.rect
            pages.append(ParsedPage(page_number=page_index, width=rect.width, height=rect.height))

            raw_blocks = page.get_text("blocks")
            text_blocks = []
            for raw_block in raw_blocks:
                x0, y0, x1, y1, text, *_rest = raw_block
                block_type = raw_block[6] if len(raw_block) > 6 else 0
                normalized = normalize_text(text)
                if block_type == 0 and normalized:
                    text_blocks.append((float(x0), float(y0), float(x1), float(y1), normalized))

            for block_index, (x0, y0, x1, y1, text) in enumerate(
                sorted(text_blocks, key=lambda item: (item[1], item[0])),
            ):
                blocks.append(
                    ParsedBlock(
                        page_number=page_index,
                        order_index=block_index,
                        x0=x0,
                        y0=y0,
                        x1=x1,
                        y1=y1,
                        text=text,
                    )
                )
                paragraphs.append(
                    ParsedParagraph(
                        page_number=page_index,
                        order_index=paragraph_index,
                        source_text=text,
                        x0=x0,
                        y0=y0,
                        x1=x1,
                        y1=y1,
                    )
                )
                paragraph_index += 1

    return ParsedPdf(pages=pages, blocks=blocks, paragraphs=paragraphs)
