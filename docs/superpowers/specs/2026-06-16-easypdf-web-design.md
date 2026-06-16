# EasyPDF Web App Design

## Summary

EasyPDF is a local-first web application for reading foreign-language academic PDFs in Chinese. Users upload a text-based English paper PDF, then read it in a two-pane web reader: the original PDF remains visible on the left through PDF.js, while a translated Chinese reading stream appears on the right. The first release focuses on reliable paragraph-level mapping, translation correction, AI-assisted explanation, and local persistence.

The app is designed as a single-user local tool for the first version, while keeping backend and data boundaries compatible with future multi-user deployment.

## Confirmed Product Decisions

- First version is a local single-user web app, with architecture prepared for future multi-user expansion.
- PDF display uses a fixed side-by-side reader: original PDF on the left, translated Chinese document on the right.
- Translation uses a hybrid workflow: parse first, translate the first pages early, then continue translating the full document in the background.
- First version supports text-based PDFs only. OCR for scanned/image-only PDFs is out of scope.
- Translated documents, reading progress, correction history, term glossary, and task states are persisted locally.
- API settings are saved in a local configuration file, not in frontend code.
- Storage uses local MySQL instead of SQLite.
- A lightweight glossary is included in the first version and injected into translation and retranslation prompts.

## Architecture

The recommended stack is:

- Frontend: Vue with PDF.js for the original PDF viewer.
- Backend: FastAPI.
- Database: local MySQL.
- File storage: local filesystem for uploaded PDFs, extracted images, and generated cache files.
- AI API: OpenAI-compatible chat/completions API configured by `API_KEY`, `BASE_URL`, and model name.

The backend is split into service boundaries:

- Document service: upload PDFs, list documents, delete documents, expose metadata.
- PDF parsing service: extract pages, text blocks, images, coordinates, and reading order.
- Translation service: create translation jobs, prioritize initial pages, continue full-document translation, retry failed paragraphs.
- Correction service: show original text, retranslate selected content with context, replace translated paragraphs, preserve revision history.
- AI assistant service: answer user questions about selected terms or passages without modifying translations.
- Settings service: manage local API settings, model selection, translation options, and MySQL connection status.
- Glossary service: manage preferred terms and translation rules.

## MySQL And Local Storage

Default database connection:

- Host: `localhost`
- Port: `3306`
- Database: `easypdf`
- User: `root`
- Password: stored only in local `.env`

The password must not be committed to Git or embedded in frontend assets.

Suggested database entities:

- `documents`: uploaded paper metadata, title, file path, status, created time, updated time.
- `pages`: per-page metadata, dimensions, parse status.
- `blocks`: extracted text and image blocks with page number, order index, coordinates, block type, and source content.
- `paragraphs`: normalized paragraph units used for translation and reader display.
- `translations`: translated paragraph text, status, model metadata, prompt version, timestamps.
- `translation_jobs`: document-level and paragraph-level task progress.
- `corrections`: manual replacement history and retranslation candidates.
- `assistant_messages`: AI Q&A history scoped to document and selected paragraph.
- `glossary_terms`: source term, preferred translation, notes, enabled flag, keep-English flag.
- `reader_positions`: last opened document, page, paragraph, and scroll position.
- `settings`: non-secret settings, with secrets stored in local configuration where possible.

Uploaded PDFs and extracted images are stored in a local application data directory. MySQL stores paths and metadata rather than binary file contents.

## PDF Parsing And Content Consistency

The original PDF is treated as the visual source of truth. The left reader displays the uploaded PDF directly through PDF.js, preserving layout, images, formulas, tables, and page appearance.

The right reader is a structured Chinese reading layer. It does not need to exactly reproduce the PDF page layout, but it must preserve:

- Paragraph reading order.
- Page ownership.
- Mapping from translated paragraph to original text.
- Image placement near the corresponding source area when extraction succeeds.
- A fallback path to jump the left PDF viewer to the original page when extraction is incomplete.

During parsing, the backend records each text or image block with page number, order index, coordinates, dimensions, block type, and source content or file path. Paragraph records are built from those blocks and become the stable units for translation, correction, and AI actions.

Images are not translated. If images are extracted successfully, they appear in the Chinese reading stream near the related paragraph. If extraction fails, the original PDF view still preserves the image, so content is not lost.

## Translation Workflow

After upload:

1. Save the original PDF.
2. Parse pages, text blocks, image blocks, and paragraph units.
3. Create a translation job for the document.
4. Prioritize the first pages so the user can start reading quickly.
5. Continue translating remaining paragraphs in the background.

Each paragraph has an independent state:

- `pending`
- `translating`
- `translated`
- `failed`
- `corrected`

This makes failures local and retryable. A failed paragraph does not block the rest of the document.

Translation prompts include:

- Source paragraph.
- Nearby context paragraphs where useful.
- Document metadata when available.
- Enabled glossary terms.
- Translation style instructions for academic Chinese.

## Reader Interaction

The reader page has:

- Top toolbar with document title, translation progress, page sync controls, settings entry, and task status.
- Left pane with PDF.js original PDF viewer.
- Right pane with Chinese paragraph stream.
- Selection-aware floating toolbar.
- Correction and AI side panel or lightweight overlay.

When the user long-presses or drags to select translated text, the UI exposes:

- Show original: display the mapped English text, page number, and source area; optionally jump the PDF viewer to that page.
- Retranslate: send original text, current translation, nearby context, and glossary to the model, then show a candidate translation in the correction panel.
- Replace translation: overwrite the paragraph translation after user confirmation and store the previous version in correction history.
- Ask AI: ask about a term, sentence, or selected passage. This is separate from retranslation and does not automatically modify the document.

## Frontend Pages

### Document Library

Shows uploaded papers, translation progress, latest reading time, failure indicators, and basic actions:

- Upload PDF.
- Continue reading.
- Open document details.
- Delete document.
- Retry failed translation tasks.

### Reader

The core reading workspace:

- Original PDF pane.
- Chinese reading pane.
- Paragraph status indicators.
- Floating selected-text toolbar.
- Correction panel for original text, retranslation result, and replacement.
- AI panel for explanations and questions.

### Settings

Contains:

- `API_KEY`, hidden by default after saving.
- `BASE_URL`.
- Model selection or manual model name input.
- MySQL connection status.
- Translation options such as concurrency, batch size, target language, and whether to keep selected terms in English.
- Local storage directory.

### Glossary

Allows users to add, edit, delete, enable, and disable term preferences:

- English term.
- Preferred Chinese translation.
- Notes.
- Keep-English option.

Glossary entries are used by translation, retranslation, and AI assistant prompts.

## Error Handling

- API configuration errors are shown in settings and task status.
- MySQL connection failures produce clear backend startup or health-check messages.
- PDF parsing failures keep the original uploaded PDF and expose a failure reason.
- Paragraph translation failures are recorded per paragraph and can be retried.
- Retranslation failures do not overwrite existing translations.
- Manual replacements always preserve revision history.

## Testing Scope

Backend tests should cover:

- Configuration loading and secret handling.
- MySQL connection and schema creation/migration.
- PDF upload validation.
- Text-based PDF parsing into pages, blocks, and paragraphs.
- Prompt construction with glossary injection.
- Translation job state transitions.
- Paragraph retranslation.
- Translation replacement and correction history.
- Reader position persistence.

Frontend tests should cover:

- Document upload flow.
- Document library rendering.
- Reader two-pane layout.
- Paragraph selection toolbar.
- Show-original flow.
- Retranslation candidate display.
- Replacement confirmation.
- Settings form save and masked API key display.
- Glossary CRUD.

## MVP Boundaries

In scope for the first implementation:

- Local single-user web app.
- Text-based PDF upload and parsing.
- Original PDF display through PDF.js.
- Chinese paragraph stream.
- Paragraph-level mapping.
- Mixed priority/background translation workflow.
- OpenAI-compatible API configuration.
- Retranslation and manual replacement.
- AI question panel.
- Local MySQL persistence.
- Lightweight glossary.

Out of scope for the first implementation:

- OCR for scanned PDFs.
- Multi-user login and permissions.
- Cloud synchronization.
- Exact Chinese reproduction of original PDF layout.
- Advanced formula recognition.
- Payment, billing, or sharing workflows.
- Desktop packaging through Electron or Tauri.

## Open Implementation Notes

- Use `.env` for local backend secrets and database credentials.
- Keep `.env`, uploaded files, generated cache data, and `.superpowers/` out of Git.
- Prefer backend APIs that include an optional user boundary internally, even though the first version uses a single local user.
- Use migration tooling rather than ad hoc database creation once implementation starts.
