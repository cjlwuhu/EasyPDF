# Reader Panels, Reading Order, And DOCX Export Design

## Summary

This iteration makes the reader's three primary content areas explicit: the original PDF, extracted English paragraphs, and translated Chinese paragraphs. Each area can be hidden independently through icon-only controls, and the remaining layout reflows automatically. It also fixes common two-column academic PDF reading order, adds Chinese-only DOCX export, and makes glossary deletion failures visible and diagnosable.

## Confirmed Decisions

- The three main reader panels are PDF original, extracted English paragraphs, and full Chinese translation.
- The selected-paragraph tools remain available as a collapsible inspector inside the translation panel.
- Panel visibility controls use icons with tooltips and accessible labels rather than visible text.
- At least one content panel must remain visible.
- Panel visibility preferences persist in browser local storage.
- DOCX export contains the document title and translated Chinese paragraphs only.
- Paragraphs without a translated result are omitted from DOCX export.
- Two-column ordering uses block geometry and falls back conservatively for pages that do not look like two-column layouts.

## Reader Layout

The reader header gains a compact view toolbar with one toggle button per panel and one DOCX download button. Toggle buttons expose pressed state through `aria-pressed`, include tooltips, and visually distinguish visible and hidden panels.

The layout is computed from the visible panel set:

- Three visible panels use the saved resizable proportions.
- Two visible panels divide the available width evenly and keep one draggable splitter.
- One visible panel fills the workspace.
- A toggle that would hide the last visible panel is disabled.

Splitters only render between adjacent visible panels. Hiding and restoring a panel does not discard the user's saved three-panel proportions.

The English and Chinese panels render the same ordered paragraph collection with different text fields. Selecting a paragraph in either panel selects the same paragraph in the other panel, updates the PDF page, and scrolls the corresponding paragraph into view. The Chinese panel contains a collapsible inspector for original text, retranslation, and AI questions so these tools remain available without becoming a fourth primary column.

## PDF Reading Order

The parser will move block ordering into a focused helper that accepts page width and extracted text block coordinates.

For each page:

1. Normalize and discard empty non-text blocks as today.
2. Detect blocks that span the page center and are wide enough to act as cross-column content.
3. Detect a two-column body only when both left and right sides contain enough blocks with separated horizontal centers.
4. Divide the page into vertical bands around cross-column blocks.
5. Within each band, order left-column blocks from top to bottom, then right-column blocks from top to bottom.
6. Insert cross-column blocks between bands according to vertical position.
7. Fall back to top-to-bottom, then left-to-right ordering for single-column or ambiguous pages.

This fixes the current `(y0, x0)` row-wise interleaving while avoiding a forced two-column interpretation for unusual layouts. The corrected ordering applies when a document is newly uploaded or reparsed; existing stored paragraphs are not silently rewritten.

## DOCX Export

The backend adds `GET /api/documents/{document_id}/translation.docx` and uses `python-docx` to generate the file in memory.

The document contains:

- The paper title as the document heading.
- Each non-empty translated paragraph in stored reading order.
- No English source text, paragraph status, page labels, or PDF imagery.

The response uses the DOCX media type and a filesystem-safe filename based on the paper title. The frontend enables the download button only when at least one translated paragraph exists. Export errors remain on the reader page and do not interrupt reading.

## Glossary Deletion

The delete endpoint has been verified directly: with the current backend running it returns HTTP 204 and removes the row. The observed failure came from the frontend proxy targeting port 8002 while no backend process was listening.

The iteration will therefore:

- Run the development backend with automatic reload.
- Remove the deleted term from frontend state immediately after HTTP 204 instead of performing a second list request.
- Show a row-level failure message when deletion fails.
- Translate connection failures into a clear backend-unavailable message.
- Keep the existing backend 404 behavior for terms that no longer exist.

## Error Handling

- Panel state is validated on load so corrupted local storage cannot hide every panel.
- Ambiguous PDF geometry uses the original single-column fallback order.
- DOCX export returns 404 for missing documents and 409 when no translated paragraphs exist.
- Failed DOCX downloads show a reader-level message.
- Failed glossary deletion keeps the row visible and displays the failure beside that row.

## Testing

Backend tests cover:

- Single-column ordering fallback.
- Two-column left-before-right ordering.
- Cross-column blocks between two-column bands.
- DOCX output containing the title and translations but not source text.
- DOCX export behavior for missing documents and documents without translations.
- Glossary delete API success and missing-term behavior.

Frontend tests cover:

- Preventing all panels from being hidden.
- Grid layout generation for one, two, and three visible panels.
- Glossary row removal after successful deletion and retained row after failure.
- DOCX download button enablement based on translated paragraph availability.

Browser verification covers desktop and narrow viewports, panel hide/show reflow, paragraph selection synchronization, DOCX download initiation, and visible glossary deletion feedback.

## Scope Boundaries

- OCR and scanned PDF layout analysis remain out of scope.
- Existing documents are not automatically reparsed because that could overwrite correction and translation state.
- DOCX export does not attempt to reproduce the PDF page layout, images, formulas, or tables.
- Advanced arbitrary multi-column layouts remain a future enhancement.
