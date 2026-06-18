export interface ParagraphRange {
  start: number;
  end: number;
}

export type ReaderPanel = "pdf" | "source" | "translation";

export interface PanelVisibility {
  pdf: boolean;
  source: boolean;
  translation: boolean;
}

export const defaultPanelVisibility: PanelVisibility = {
  pdf: true,
  source: true,
  translation: true
};

export function normalizeVisiblePanels(value: unknown): PanelVisibility {
  if (!value || typeof value !== "object") return { ...defaultPanelVisibility };

  const candidate = value as Partial<Record<ReaderPanel, unknown>>;
  if (
    typeof candidate.pdf !== "boolean" ||
    typeof candidate.source !== "boolean" ||
    typeof candidate.translation !== "boolean"
  ) {
    return { ...defaultPanelVisibility };
  }

  const normalized: PanelVisibility = {
    pdf: candidate.pdf,
    source: candidate.source,
    translation: candidate.translation
  };
  if (!normalized.pdf && !normalized.source && !normalized.translation) {
    normalized.pdf = true;
  }
  return normalized;
}

export function visiblePanels(visibility: PanelVisibility): ReaderPanel[] {
  return (["pdf", "source", "translation"] as const).filter((panel) => visibility[panel]);
}

export function visiblePanelGrid(panels: ReaderPanel[]): string {
  if (panels.length <= 1) return "minmax(0, 1fr)";
  if (panels.length === 2) return "minmax(0, 1fr) 8px minmax(0, 1fr)";
  return "minmax(0, 38fr) 8px minmax(0, 38fr) 8px minmax(0, 24fr)";
}

export function hasTranslatedParagraphs<T extends { translated_text: string }>(paragraphs: T[]): boolean {
  return paragraphs.some((paragraph) => paragraph.translated_text.trim().length > 0);
}

export function sortParagraphsByReadingOrder<
  T extends { page_number: number; order_index: number; reading_order: number }
>(paragraphs: T[]): T[] {
  return [...paragraphs].sort(
    (left, right) =>
      left.reading_order - right.reading_order ||
      left.page_number - right.page_number ||
      left.order_index - right.order_index
  );
}

export function clampPageNumber(pageNumber: number, totalPages: number): number {
  const safeTotal = Math.max(1, totalPages);
  if (!Number.isFinite(pageNumber)) return 1;
  return Math.min(Math.max(Math.trunc(pageNumber), 1), safeTotal);
}

export function normalizeParagraphRange(
  firstOrderIndex: number | null,
  secondOrderIndex: number | null
): ParagraphRange | null {
  if (firstOrderIndex === null || secondOrderIndex === null) return null;
  return {
    start: Math.min(firstOrderIndex, secondOrderIndex),
    end: Math.max(firstOrderIndex, secondOrderIndex)
  };
}

export function isParagraphInRange(orderIndex: number, range: ParagraphRange | null): boolean {
  if (!range) return false;
  return orderIndex >= range.start && orderIndex <= range.end;
}
