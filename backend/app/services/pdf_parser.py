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


def order_text_blocks(blocks: list[ParsedBlock], page_width: float) -> list[ParsedBlock]:
    fallback = sorted(blocks, key=lambda item: (item.y0, item.x0))
    if not blocks or page_width <= 0:
        return fallback

    midpoint = page_width / 2
    spanning = [
        item
        for item in blocks
        if item.x0 < midpoint < item.x1 and (item.x1 - item.x0) >= page_width * 0.55
    ]
    column_blocks = [item for item in blocks if item not in spanning]
    left_blocks = [item for item in column_blocks if (item.x0 + item.x1) / 2 < midpoint]
    right_blocks = [item for item in column_blocks if (item.x0 + item.x1) / 2 >= midpoint]

    if not left_blocks or not right_blocks:
        return fallback

    def order_band(items: list[ParsedBlock]) -> list[ParsedBlock]:
        left = sorted(
            (item for item in items if (item.x0 + item.x1) / 2 < midpoint),
            key=lambda item: (item.y0, item.x0),
        )
        right = sorted(
            (item for item in items if (item.x0 + item.x1) / 2 >= midpoint),
            key=lambda item: (item.y0, item.x0),
        )
        return [*left, *right]

    ordered: list[ParsedBlock] = []
    remaining = list(column_blocks)
    for spanning_block in sorted(spanning, key=lambda item: (item.y0, item.x0)):
        spanning_midpoint = (spanning_block.y0 + spanning_block.y1) / 2
        before = [item for item in remaining if (item.y0 + item.y1) / 2 < spanning_midpoint]
        ordered.extend(order_band(before))
        ordered.append(spanning_block)
        remaining = [item for item in remaining if item not in before]

    ordered.extend(order_band(remaining))
    return ordered


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

            page_blocks = [
                ParsedBlock(
                    page_number=page_index,
                    order_index=0,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    text=text,
                )
                for x0, y0, x1, y1, text in text_blocks
            ]

            for block_index, ordered_block in enumerate(order_text_blocks(page_blocks, rect.width)):
                blocks.append(
                    ParsedBlock(
                        page_number=page_index,
                        order_index=block_index,
                        x0=ordered_block.x0,
                        y0=ordered_block.y0,
                        x1=ordered_block.x1,
                        y1=ordered_block.y1,
                        text=ordered_block.text,
                    )
                )
                paragraphs.append(
                    ParsedParagraph(
                        page_number=page_index,
                        order_index=paragraph_index,
                        source_text=ordered_block.text,
                        x0=ordered_block.x0,
                        y0=ordered_block.y0,
                        x1=ordered_block.x1,
                        y1=ordered_block.y1,
                    )
                )
                paragraph_index += 1

    return ParsedPdf(pages=pages, blocks=blocks, paragraphs=paragraphs)
