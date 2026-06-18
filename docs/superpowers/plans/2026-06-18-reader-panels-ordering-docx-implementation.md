# Reader Panels, Reading Order, And DOCX Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver hideable reader panels, correct common two-column PDF reading order, reliable glossary deletion feedback, and Chinese-only DOCX export.

**Architecture:** Keep layout state and deterministic grid calculations in frontend utilities, then render PDF/source/translation as three explicit synchronized panels. Move PDF block ordering and DOCX generation into focused backend services so both behaviors are testable without HTTP or browser setup. Existing paragraph APIs remain the shared data contract.

**Tech Stack:** Vue 3, TypeScript, Lucide Vue, Vite, Vitest, FastAPI, SQLAlchemy, PyMuPDF, python-docx, Pytest.

---

## File Structure

- Modify `frontend/src/utils/readerWorkbench.ts`: panel visibility validation and dynamic grid helpers.
- Modify `frontend/tests/reader-workbench.test.ts`: panel visibility and grid tests.
- Modify `frontend/src/views/ReaderView.vue`: explicit PDF/source/translation panels, icon toolbar, synchronized selection, collapsible inspector, DOCX download.
- Modify `frontend/package.json` and `frontend/package-lock.json`: add `lucide-vue-next`.
- Create `frontend/src/utils/glossary.ts`: immutable row removal and readable API error mapping.
- Create `frontend/tests/glossary.test.ts`: glossary helper tests.
- Modify `frontend/src/views/GlossaryView.vue`: immediate row removal and row-level error feedback.
- Modify `frontend/src/api/client.ts`: typed download helper and shared API error type.
- Modify `scripts/dev.ps1`: run backend with `--reload`.
- Modify `backend/app/services/pdf_parser.py`: conservative geometry-based reading order.
- Modify `backend/tests/test_pdf_parser.py`: single-column, two-column, and spanning-block ordering tests.
- Create `backend/app/services/docx_export.py`: build translated DOCX bytes and safe download names.
- Create `backend/tests/test_docx_export.py`: inspect generated DOCX content.
- Modify `backend/app/api/routes/documents.py`: expose translated DOCX download route.
- Modify `backend/pyproject.toml`: add `python-docx`.

---

### Task 1: Glossary Delete Reliability

**Files:**
- Create: `frontend/src/utils/glossary.ts`
- Create: `frontend/tests/glossary.test.ts`
- Modify: `frontend/src/views/GlossaryView.vue`
- Modify: `frontend/src/api/client.ts`
- Modify: `scripts/dev.ps1`

- [ ] **Step 1: Write failing frontend helper tests**

```ts
import { describe, expect, it } from "vitest";
import { describeGlossaryDeleteError, removeGlossaryTerm } from "../src/utils/glossary";

describe("glossary deletion", () => {
  it("removes only the deleted term", () => {
    const terms = [{ id: 1 }, { id: 2 }];
    expect(removeGlossaryTerm(terms, 1)).toEqual([{ id: 2 }]);
  });

  it("explains backend connection failures", () => {
    expect(describeGlossaryDeleteError(new TypeError("Failed to fetch")))
      .toBe("Backend is unavailable. Start EasyPDF and try again.");
  });
});
```

- [ ] **Step 2: Run the test and verify RED**

Run: `cd frontend; npm.cmd test -- glossary.test.ts`

Expected: FAIL because `src/utils/glossary.ts` does not exist.

- [ ] **Step 3: Implement the glossary helpers**

```ts
export function removeGlossaryTerm<T extends { id: number }>(terms: T[], termId: number): T[] {
  return terms.filter((term) => term.id !== termId);
}

export function describeGlossaryDeleteError(error: unknown): string {
  if (error instanceof TypeError) return "Backend is unavailable. Start EasyPDF and try again.";
  return error instanceof Error ? error.message : "Failed to delete glossary term";
}
```

- [ ] **Step 4: Wire immediate removal and row-level errors**

Update `GlossaryView.vue` so a successful 204 assigns `terms.value = removeGlossaryTerm(terms.value, termId)`. Store errors in `deleteErrors: Record<number, string>` and render the matching message beside the row. Keep the row when the request fails.

- [ ] **Step 5: Enable backend reload in development**

Change the backend command in `scripts/dev.ps1` to include `--reload`:

```powershell
conda run -n lang-chain01 python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

- [ ] **Step 6: Verify GREEN**

Run: `cd frontend; npm.cmd test -- glossary.test.ts`

Expected: two tests pass.

---

### Task 2: Two-Column PDF Reading Order

**Files:**
- Modify: `backend/app/services/pdf_parser.py`
- Modify: `backend/tests/test_pdf_parser.py`

- [ ] **Step 1: Write failing ordering tests**

Add tests that construct `ParsedBlock` values and call `order_text_blocks(blocks, page_width=600)`:

```python
def block(text, x0, y0, x1, y1):
    return ParsedBlock(1, 0, x0, y0, x1, y1, text)


def test_two_column_order_reads_left_column_before_right():
    blocks = [
        block("right top", 330, 80, 560, 120),
        block("left bottom", 40, 180, 270, 220),
        block("left top", 40, 80, 270, 120),
        block("right bottom", 330, 180, 560, 220),
    ]
    assert [item.text for item in order_text_blocks(blocks, 600)] == [
        "left top", "left bottom", "right top", "right bottom"
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
    assert [item.text for item in order_text_blocks(blocks, 600)] == [
        "title", "left", "right", "figure caption", "left after", "right after"
    ]
```

Also add a single-column test that expects `(y0, x0)` ordering.

- [ ] **Step 2: Run parser tests and verify RED**

Run: `cd backend; conda run -n lang-chain01 python -m pytest tests/test_pdf_parser.py -v`

Expected: FAIL because `order_text_blocks` does not exist.

- [ ] **Step 3: Implement conservative ordering**

Add `order_text_blocks(blocks, page_width)` that:

- Classifies a block as spanning when it crosses the page midpoint and occupies at least 55% of page width.
- Requires at least two left and two right non-spanning blocks before selecting two-column mode.
- Falls back to `(y0, x0)` otherwise.
- Splits non-spanning blocks into vertical bands around spanning blocks.
- Orders each band by left-column `(y0, x0)` followed by right-column `(y0, x0)`.

Use this helper in `parse_pdf` before assigning block and paragraph order indices.

- [ ] **Step 4: Run parser tests and verify GREEN**

Run: `cd backend; conda run -n lang-chain01 python -m pytest tests/test_pdf_parser.py -v`

Expected: all parser tests pass.

---

### Task 3: Hideable Reader Panels

**Files:**
- Modify: `frontend/src/utils/readerWorkbench.ts`
- Modify: `frontend/tests/reader-workbench.test.ts`
- Modify: `frontend/src/views/ReaderView.vue`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Write failing panel-state tests**

```ts
import { normalizeVisiblePanels, visiblePanelGrid } from "../src/utils/readerWorkbench";

expect(normalizeVisiblePanels({ pdf: false, source: false, translation: false }))
  .toEqual({ pdf: true, source: false, translation: false });
expect(visiblePanelGrid(["pdf"])).toBe("minmax(0, 1fr)");
expect(visiblePanelGrid(["pdf", "translation"])).toBe("minmax(0, 1fr) 8px minmax(0, 1fr)");
expect(visiblePanelGrid(["pdf", "source", "translation"]))
  .toBe("minmax(0, 38fr) 8px minmax(0, 38fr) 8px minmax(0, 24fr)");
```

- [ ] **Step 2: Run tests and verify RED**

Run: `cd frontend; npm.cmd test -- reader-workbench.test.ts`

Expected: FAIL because the new exports do not exist.

- [ ] **Step 3: Implement panel helpers**

Define `ReaderPanel = "pdf" | "source" | "translation"`, `PanelVisibility`, `normalizeVisiblePanels`, and `visiblePanelGrid`. Validation always restores PDF when persisted state hides every panel.

- [ ] **Step 4: Install Lucide Vue**

Run: `cd frontend; npm.cmd install lucide-vue-next`

- [ ] **Step 5: Refactor the reader template**

Update `ReaderView.vue` to:

- Render icon-only `FileText`, `TextSelect`, and `Languages` toggle buttons with `title`, `aria-label`, and `aria-pressed`.
- Persist panel visibility under `easypdf.reader.panels`.
- Render three explicit panels: `PdfPane`, source paragraphs using `source_text`, and translated paragraphs using `translated_text`.
- Disable the last visible panel's toggle.
- Render splitters only between visible adjacent panels.
- Keep selection shared by paragraph id and scroll matching source/translation elements into view.
- Move selected-paragraph actions into a collapsible inspector at the top of the translation panel.

- [ ] **Step 6: Verify GREEN**

Run: `cd frontend; npm.cmd test -- reader-workbench.test.ts`

Expected: all reader workbench tests pass.

---

### Task 4: Chinese-Only DOCX Export

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/app/services/docx_export.py`
- Create: `backend/tests/test_docx_export.py`
- Modify: `backend/app/api/routes/documents.py`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/views/ReaderView.vue`

- [ ] **Step 1: Add python-docx to the active environment and metadata**

Add `python-docx>=1.1` to `backend/pyproject.toml`, then run:

`conda run -n lang-chain01 python -m pip install "python-docx>=1.1"`

- [ ] **Step 2: Write failing DOCX service tests**

```python
from io import BytesIO
from docx import Document as DocxDocument
from app.services.docx_export import build_translation_docx, safe_docx_filename


def test_docx_contains_title_and_translations_only():
    payload = build_translation_docx("Paper", ["第一段译文", "第二段译文"])
    document = DocxDocument(BytesIO(payload))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "Paper" in text
    assert "第一段译文" in text
    assert "第二段译文" in text


def test_safe_docx_filename_removes_windows_reserved_characters():
    assert safe_docx_filename('A/B:C*?') == "A_B_C___translated.docx"
```

- [ ] **Step 3: Run DOCX tests and verify RED**

Run: `cd backend; conda run -n lang-chain01 python -m pytest tests/test_docx_export.py -v`

Expected: FAIL because `app.services.docx_export` does not exist.

- [ ] **Step 4: Implement DOCX generation**

Create functions:

```python
def build_translation_docx(title: str, translations: list[str]) -> bytes:
    document = DocxDocument()
    document.add_heading(title, level=0)
    for translation in translations:
        if translation.strip():
            document.add_paragraph(translation.strip())
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def safe_docx_filename(title: str) -> str:
    safe_title = re.sub(r'[<>:"/\\|?*]', "_", title).strip(" .") or "translation"
    return f"{safe_title}_translated.docx"
```

- [ ] **Step 5: Add the download route**

Add `GET /api/documents/{document_id}/translation.docx`. Fetch the document, sort paragraphs by `order_index`, include only non-empty `translated_text`, return 409 when none exist, and stream the bytes with the DOCX media type and UTF-8 filename header.

- [ ] **Step 6: Add the frontend download button**

Add an icon-only `Download` button to the reader toolbar. Disable it when no paragraph has non-empty `translated_text`. Use a blob download helper so non-2xx responses become visible reader errors.

- [ ] **Step 7: Verify GREEN**

Run: `cd backend; conda run -n lang-chain01 python -m pytest tests/test_docx_export.py -v`

Expected: all DOCX tests pass.

---

### Task 5: Full Verification And Browser QA

**Files:**
- Verify all files changed above.

- [ ] **Step 1: Run backend tests**

Run: `cd backend; conda run -n lang-chain01 python -m pytest -v`

Expected: all tests pass.

- [ ] **Step 2: Run frontend tests and build**

Run: `cd frontend; npm.cmd test`

Run: `cd frontend; npm.cmd run build`

Expected: all tests and TypeScript/Vite build pass.

- [ ] **Step 3: Start both services**

Run: `powershell -ExecutionPolicy Bypass -File scripts/dev.ps1`

Expected: backend health responds on port 8002 and frontend loads on an available Vite port.

- [ ] **Step 4: Browser verification**

Verify at desktop and narrow widths:

- Each icon toggle hides and restores its panel.
- Two panels share space evenly and one panel fills the workspace.
- The final visible panel cannot be hidden.
- Source/translation selection highlights the corresponding paragraph and updates the PDF page.
- DOCX download begins and produces a readable file.
- Glossary deletion removes the row; a stopped backend produces a visible row error.

- [ ] **Step 5: Review Git diff**

Run: `git status --short` and `git diff --check`.

Expected: only intended source, test, dependency, and plan files are changed; no whitespace errors.

---

## Self-Review

- Spec coverage: all confirmed panel, parser, DOCX, glossary, error, and testing requirements map to tasks.
- Type consistency: frontend panel names are `pdf`, `source`, and `translation` throughout.
- API consistency: DOCX endpoint is `/api/documents/{document_id}/translation.docx` throughout.
- Scope: existing stored paragraphs are not automatically rewritten; OCR and exact PDF layout export remain excluded.
