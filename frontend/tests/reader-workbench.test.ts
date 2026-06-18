import { describe, expect, it } from "vitest";

import {
  clampPageNumber,
  hasTranslatedParagraphs,
  isParagraphInRange,
  normalizeParagraphRange,
  normalizeVisiblePanels,
  sortParagraphsByReadingOrder,
  visiblePanelGrid
} from "../src/utils/readerWorkbench";

describe("reader workbench helpers", () => {
  it("clamps requested PDF pages to the loaded document bounds", () => {
    expect(clampPageNumber(0, 10)).toBe(1);
    expect(clampPageNumber(6, 10)).toBe(6);
    expect(clampPageNumber(14, 10)).toBe(10);
    expect(clampPageNumber(4, 0)).toBe(1);
  });

  it("normalizes paragraph range endpoints regardless of click order", () => {
    expect(normalizeParagraphRange(8, 3)).toEqual({ start: 3, end: 8 });
    expect(normalizeParagraphRange(2, 5)).toEqual({ start: 2, end: 5 });
    expect(normalizeParagraphRange(null, 5)).toBeNull();
    expect(normalizeParagraphRange(2, null)).toBeNull();
  });

  it("detects whether a paragraph belongs to the chosen inclusive range", () => {
    const range = { start: 3, end: 6 };

    expect(isParagraphInRange(2, range)).toBe(false);
    expect(isParagraphInRange(3, range)).toBe(true);
    expect(isParagraphInRange(5, range)).toBe(true);
    expect(isParagraphInRange(6, range)).toBe(true);
    expect(isParagraphInRange(7, range)).toBe(false);
    expect(isParagraphInRange(4, null)).toBe(false);
  });

  it("restores the PDF panel when persisted state hides every panel", () => {
    expect(normalizeVisiblePanels({ pdf: false, source: false, translation: false })).toEqual({
      pdf: true,
      source: false,
      translation: false
    });
  });

  it("normalizes malformed persisted panel state", () => {
    expect(normalizeVisiblePanels({ pdf: "yes", source: true })).toEqual({
      pdf: true,
      source: true,
      translation: true
    });
  });

  it("builds stable grids for one, two, and three visible panels", () => {
    expect(visiblePanelGrid(["pdf"])).toBe("minmax(0, 1fr)");
    expect(visiblePanelGrid(["pdf", "translation"])).toBe(
      "minmax(0, 1fr) 8px minmax(0, 1fr)"
    );
    expect(visiblePanelGrid(["pdf", "source", "translation"])).toBe(
      "minmax(0, 38fr) 8px minmax(0, 38fr) 8px minmax(0, 24fr)"
    );
  });

  it("enables export only when at least one translation is nonempty", () => {
    expect(hasTranslatedParagraphs([{ translated_text: "" }, { translated_text: "  " }])).toBe(false);
    expect(hasTranslatedParagraphs([{ translated_text: "" }, { translated_text: "译文" }])).toBe(true);
  });

  it("uses backend reading order for legacy documents", () => {
    const paragraphs = [
      { page_number: 1, order_index: 0, reading_order: 2 },
      { page_number: 1, order_index: 2, reading_order: 0 },
      { page_number: 1, order_index: 1, reading_order: 1 }
    ];

    expect(sortParagraphsByReadingOrder(paragraphs).map((paragraph) => paragraph.order_index)).toEqual([
      2, 1, 0
    ]);
  });
});
