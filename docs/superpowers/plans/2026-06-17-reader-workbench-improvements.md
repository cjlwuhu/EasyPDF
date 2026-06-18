# Reader Workbench Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the translation reader so PDF pages follow reading position, paragraph range translation is independent from paragraph inspection, pane widths are resizable, and glossary terms can be deleted.

**Architecture:** Keep the reader as a Vue single-view workbench. Move small deterministic reader behaviors into a tested utility module, upgrade `PdfPane` to accept a page number plus manual navigation events, and add a fixed third column for selected paragraph details. Add a narrow glossary delete API endpoint and wire it to the existing glossary screen.

**Tech Stack:** Vue 3, TypeScript, Vite/Vitest, PDF.js, FastAPI, SQLAlchemy, Pytest.

---

## File Structure

- Create `frontend/src/utils/readerWorkbench.ts`: pure helpers for clamping page numbers, range normalization, and selected range membership.
- Modify `frontend/tests/reader-workbench.test.ts`: tests for reader page/range helpers.
- Modify `frontend/src/components/PdfPane.vue`: render a requested page, show current/total page controls, emit manual page changes.
- Modify `frontend/src/views/ReaderView.vue`: add selected page sync, range start/end buttons, fixed side workbench, and draggable pane layout.
- Modify `frontend/src/api/client.ts`: add `apiDelete`.
- Modify `frontend/src/views/GlossaryView.vue`: add delete buttons and reload behavior.
- Modify `backend/tests/test_glossary.py`: add service-level deletion coverage.
- Modify `backend/app/services/glossary.py`: add `delete_term`.
- Modify `backend/app/api/routes/glossary.py`: add `DELETE /api/glossary/{term_id}`.

---

## Tasks

### Task 1: Reader Utility Tests

- [ ] Write failing tests in `frontend/tests/reader-workbench.test.ts` for clamping page numbers, normalizing range endpoints, and detecting selected range membership.
- [ ] Run `npm test -- reader-workbench.test.ts` and confirm the helper module is missing.
- [ ] Add `frontend/src/utils/readerWorkbench.ts`.
- [ ] Re-run the same test and confirm it passes.

### Task 2: Glossary Delete Tests

- [ ] Add a failing test to `backend/tests/test_glossary.py` proving deleting a term removes it from `list_terms`.
- [ ] Run `pytest tests/test_glossary.py -v` and confirm `delete_term` is missing.
- [ ] Add `delete_term` to `backend/app/services/glossary.py` and a `DELETE` route in `backend/app/api/routes/glossary.py`.
- [ ] Re-run `pytest tests/test_glossary.py -v` and confirm it passes.

### Task 3: Reader Workbench UI

- [ ] Modify `PdfPane.vue` so it accepts `pageNumber`, clamps page navigation to PDF bounds, emits `update:pageNumber`, and renders manual previous/next controls.
- [ ] Modify `ReaderView.vue` so selecting a paragraph updates the PDF page, manual PDF page changes do not break later paragraph sync, and the selected paragraph details live in a fixed right workbench.
- [ ] Add range selection state in `ReaderView.vue`: `setRangeStart`, `setRangeEnd`, normalized selected range highlighting, and a `translateSelectedRange` action that retranslates each paragraph in the chosen inclusive range.
- [ ] Add draggable splitters between PDF, paragraph list, and detail workbench using CSS grid percentages with min/max clamps.
- [ ] Run `npm test -- reader-workbench.test.ts`.

### Task 4: Glossary Delete UI

- [ ] Add `apiDelete` to `frontend/src/api/client.ts`.
- [ ] Add a delete button per glossary row in `GlossaryView.vue`.
- [ ] Disable only the row being deleted while the request is active, then reload terms.
- [ ] Run `npm test`.

### Task 5: Verification

- [ ] Run backend glossary tests: `pytest tests/test_glossary.py -v`.
- [ ] Run frontend tests: `npm test`.
- [ ] Run frontend build: `npm run build`.
- [ ] Start the frontend dev server and inspect the reader/glossary UI in the in-app browser.

---

## Self-Review

- The plan covers all five requested changes.
- No new database migration is required because glossary records already exist and delete is a row removal.
- The range translation action reuses the existing paragraph retranslation endpoint to avoid adding a backend batch endpoint before the user validates the workflow.
