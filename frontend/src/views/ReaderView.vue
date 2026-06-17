<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiGet, apiPost } from "../api/client";
import PdfPane from "../components/PdfPane.vue";
import SelectionToolbar from "../components/SelectionToolbar.vue";
import StatusBadge from "../components/StatusBadge.vue";
import type { DocumentDetail, Paragraph, ParagraphStatus, TranslationJob } from "../types";
import { formatTranslationJobProgress } from "../utils/translationJob";

const route = useRoute();

const documentDetail = ref<DocumentDetail | null>(null);
const loading = ref(true);
const error = ref("");
const selectedParagraph = ref<Paragraph | null>(null);
const selectedText = ref("");
const showOriginal = ref(false);
const assistantQuestion = ref("");
const assistantAnswer = ref("");
const assistantError = ref("");
const retranslateError = ref("");
const retranslateLoading = ref(false);
const assistantLoading = ref(false);
const translationJob = ref<TranslationJob | null>(null);
const translationJobError = ref("");
const startTranslationLoading = ref(false);
let translationPoller: number | undefined;

const documentId = computed(() => String(route.params.id));
const pdfUrl = computed(() => `/api/documents/${documentId.value}/file`);
const paragraphs = computed(() => documentDetail.value?.paragraphs ?? []);
const sortedParagraphs = computed(() =>
  [...paragraphs.value].sort(
    (left, right) => left.page_number - right.page_number || left.order_index - right.order_index
  )
);
const selectedSourceText = computed(() => selectedParagraph.value?.source_text ?? "");
const selectedTranslationText = computed(
  () => selectedParagraph.value?.translated_text || selectedParagraph.value?.source_text || ""
);
const translationJobProgress = computed(() =>
  translationJob.value ? formatTranslationJobProgress(translationJob.value) : null
);
const hasTranslatableParagraphs = computed(() =>
  sortedParagraphs.value.some((paragraph) => paragraph.status === "pending" || paragraph.status === "failed")
);

async function loadDocument() {
  loading.value = true;
  error.value = "";
  try {
    documentDetail.value = await apiGet<DocumentDetail>(`/api/documents/${documentId.value}`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load document";
  } finally {
    loading.value = false;
  }
}

function selectParagraph(paragraph: Paragraph) {
  selectedParagraph.value = paragraph;
  selectedText.value = paragraph.translated_text || paragraph.source_text;
  showOriginal.value = false;
  assistantAnswer.value = "";
  assistantError.value = "";
  retranslateError.value = "";
}

async function retranslateSelectedParagraph() {
  if (!selectedParagraph.value) return;

  retranslateLoading.value = true;
  retranslateError.value = "";
  try {
    const result = await apiPost<{ paragraph_id: number; translated_text: string; status: string }>(
      "/api/translations/paragraph",
      { paragraph_id: selectedParagraph.value.id }
    );
    selectedParagraph.value.translated_text = result.translated_text;
    selectedParagraph.value.status = result.status as ParagraphStatus;
    selectedText.value = result.translated_text;
  } catch (err) {
    retranslateError.value = err instanceof Error ? err.message : "Failed to retranslate paragraph";
  } finally {
    retranslateLoading.value = false;
  }
}

function stopTranslationPolling() {
  if (translationPoller !== undefined) {
    window.clearInterval(translationPoller);
    translationPoller = undefined;
  }
}

function isFinishedJob(status: string): boolean {
  return status === "completed" || status === "completed_with_errors";
}

async function pollTranslationJob(jobId: number) {
  try {
    translationJob.value = await apiGet<TranslationJob>(`/api/translations/jobs/${jobId}`);
    if (isFinishedJob(translationJob.value.status)) {
      stopTranslationPolling();
      await loadDocument();
    }
  } catch (err) {
    stopTranslationPolling();
    translationJobError.value = err instanceof Error ? err.message : "Failed to refresh translation status";
  }
}

function startTranslationPolling(jobId: number) {
  stopTranslationPolling();
  void pollTranslationJob(jobId);
  translationPoller = window.setInterval(() => {
    void pollTranslationJob(jobId);
  }, 1800);
}

async function startDocumentTranslation() {
  startTranslationLoading.value = true;
  translationJobError.value = "";
  try {
    const result = await apiPost<{ job_id: number; status: string; total_count: number }>(
      `/api/translations/documents/${documentId.value}/start`,
      {}
    );
    translationJob.value = {
      job_id: result.job_id,
      document_id: Number(documentId.value),
      status: result.status,
      total_count: result.total_count,
      completed_count: 0,
      failed_count: 0
    };
    if (result.total_count > 0) {
      startTranslationPolling(result.job_id);
    } else {
      await loadDocument();
    }
  } catch (err) {
    translationJobError.value = err instanceof Error ? err.message : "Failed to start translation";
  } finally {
    startTranslationLoading.value = false;
  }
}

async function askAiAboutSelection() {
  if (!selectedParagraph.value) return;

  assistantLoading.value = true;
  assistantError.value = "";
  assistantAnswer.value = "";
  try {
    const result = await apiPost<{ answer: string }>("/api/assistant/ask", {
      question: assistantQuestion.value.trim() || "Explain this translated paragraph and note any translation issues.",
      selected_text: selectedText.value,
      source_text: selectedParagraph.value.source_text
    });
    assistantAnswer.value = result.answer;
  } catch (err) {
    assistantError.value = err instanceof Error ? err.message : "Failed to ask AI";
  } finally {
    assistantLoading.value = false;
  }
}

onMounted(loadDocument);
onBeforeUnmount(stopTranslationPolling);
</script>

<template>
  <section class="reader-view">
    <header class="reader-header">
      <div>
        <p class="eyebrow">Reader</p>
        <h1>{{ documentDetail?.title || "PDF Reader" }}</h1>
      </div>
      <div class="reader-meta">
        <span>{{ documentDetail?.original_filename || `Document ${documentId}` }}</span>
        <StatusBadge v-if="documentDetail" :status="documentDetail.status" />
      </div>
    </header>

    <p v-if="error" class="alert">{{ error }}</p>

    <div class="reader-grid">
      <aside class="pdf-column" aria-label="Original PDF">
        <PdfPane :file-url="pdfUrl" />
      </aside>

      <main class="translation-column" aria-label="Translated paragraphs">
        <div class="translation-head">
          <div>
            <p class="eyebrow">Translation Stream</p>
            <h2>{{ sortedParagraphs.length }} paragraphs</h2>
          </div>
          <div class="translation-actions">
            <button
              class="primary-button"
              type="button"
              :disabled="startTranslationLoading || !hasTranslatableParagraphs"
              @click="startDocumentTranslation"
            >
              {{ startTranslationLoading ? "Starting..." : "生成中文翻译" }}
            </button>
            <span v-if="selectedParagraph" class="selection-chip">Selected {{ selectedParagraph.order_index + 1 }}</span>
          </div>
        </div>

        <div v-if="translationJobProgress" class="job-progress" aria-live="polite">
          <div class="progress-text">
            <span>{{ translationJobProgress.label }}</span>
            <span>{{ translationJobProgress.percent }}%</span>
          </div>
          <div class="progress-track">
            <span :style="{ width: `${translationJobProgress.percent}%` }"></span>
          </div>
        </div>
        <p v-if="translationJobError" class="alert compact">{{ translationJobError }}</p>

        <p v-if="loading" class="muted-state">Loading document...</p>
        <p v-else-if="!sortedParagraphs.length" class="muted-state">No translated paragraphs are available yet.</p>

        <div v-else class="paragraph-list">
          <button
            v-for="paragraph in sortedParagraphs"
            :key="paragraph.id"
            class="paragraph-card"
            :class="{ selected: selectedParagraph?.id === paragraph.id }"
            type="button"
            @click="selectParagraph(paragraph)"
          >
            <span class="paragraph-meta">
              <span>Page {{ paragraph.page_number }}</span>
              <StatusBadge :status="paragraph.status" />
            </span>
            <span class="paragraph-text">{{ paragraph.translated_text || paragraph.source_text }}</span>
          </button>
        </div>

        <section v-if="selectedParagraph" class="selection-panel" aria-label="Selected paragraph details">
          <SelectionToolbar
            @show-original="showOriginal = !showOriginal"
            @retranslate="retranslateSelectedParagraph"
            @ask-ai="askAiAboutSelection"
          />

          <p v-if="retranslateLoading" class="muted-line">Retranslating paragraph...</p>
          <p v-if="retranslateError" class="alert compact">{{ retranslateError }}</p>

          <div v-if="showOriginal" class="detail-panel">
            <p class="panel-label">Original</p>
            <p>{{ selectedSourceText }}</p>
          </div>

          <div class="detail-panel">
            <p class="panel-label">Ask AI</p>
            <textarea
              v-model="assistantQuestion"
              rows="3"
              placeholder="Ask about the selected translation..."
            ></textarea>
            <button class="primary-button" type="button" :disabled="assistantLoading" @click="askAiAboutSelection">
              {{ assistantLoading ? "Asking..." : "Ask" }}
            </button>
            <p v-if="assistantError" class="alert compact">{{ assistantError }}</p>
            <p v-if="assistantAnswer" class="assistant-answer">{{ assistantAnswer }}</p>
          </div>

          <div class="detail-panel">
            <p class="panel-label">Selected text</p>
            <p>{{ selectedTranslationText }}</p>
          </div>
        </section>
      </main>
    </div>
  </section>
</template>

<style scoped>
.reader-view {
  min-height: 100vh;
  padding: 28px;
}

.reader-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #63716a;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1,
h2 {
  margin: 0;
  color: #1f2a25;
  line-height: 1.2;
}

h1 {
  font-size: 30px;
}

h2 {
  font-size: 18px;
}

.reader-meta {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 0;
  color: #62675f;
}

.reader-meta span:first-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.95fr) minmax(380px, 1.05fr);
  gap: 18px;
  align-items: start;
}

.pdf-column,
.translation-column {
  min-width: 0;
}

.translation-column {
  display: grid;
  gap: 12px;
}

.translation-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 14px 16px;
  background: #fffdfa;
}

.selection-chip {
  border-radius: 4px;
  padding: 5px 8px;
  background: #e2ebe6;
  color: #244c3d;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.translation-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.job-progress {
  display: grid;
  gap: 8px;
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 12px 14px;
  background: #fffdfa;
}

.progress-text {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #3c4a42;
  font-size: 13px;
  font-weight: 700;
}

.progress-track {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e9e3d8;
}

.progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #244c3d;
  transition: width 160ms ease;
}

.paragraph-list {
  display: grid;
  gap: 10px;
  max-height: 55vh;
  overflow: auto;
  padding-right: 4px;
}

.paragraph-card {
  display: grid;
  gap: 9px;
  width: 100%;
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 14px;
  background: #fffdfa;
  color: #26332c;
  text-align: left;
}

.paragraph-card:hover,
.paragraph-card:focus-visible,
.paragraph-card.selected {
  border-color: #8ca897;
  background: #f6faf7;
  outline: none;
}

.paragraph-card.selected {
  box-shadow: inset 3px 0 0 #244c3d;
}

.paragraph-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #62675f;
  font-size: 12px;
  font-weight: 700;
}

.paragraph-text {
  color: #26332c;
  line-height: 1.7;
}

.selection-panel,
.detail-panel {
  display: grid;
  gap: 10px;
}

.selection-panel {
  border-top: 1px solid #d8d3c8;
  padding-top: 12px;
}

.detail-panel {
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 12px;
  background: #fffdfa;
}

.detail-panel p {
  margin: 0;
  color: #40473f;
  line-height: 1.7;
}

.panel-label {
  color: #63716a !important;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

textarea {
  width: 100%;
  min-width: 0;
  resize: vertical;
  border: 1px solid #d8d3c8;
  border-radius: 6px;
  padding: 10px 11px;
  background: #fbfaf7;
  color: #26332c;
  font-size: 14px;
  line-height: 1.5;
}

textarea:focus {
  border-color: #244c3d;
  outline: none;
}

.primary-button {
  justify-self: start;
  min-height: 36px;
  border: 1px solid #244c3d;
  border-radius: 6px;
  padding: 0 14px;
  background: #244c3d;
  color: #fffdfa;
  font-weight: 700;
}

.primary-button:disabled {
  cursor: wait;
  opacity: 0.68;
}

.alert {
  margin: 0 0 12px;
  border: 1px solid #e4b5ae;
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff2ef;
  color: #8a3028;
}

.compact {
  margin: 0;
}

.muted-state,
.muted-line {
  margin: 0;
  color: #62675f;
}

.muted-state {
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 28px 16px;
  background: #fffdfa;
}

.assistant-answer {
  border-top: 1px solid #eee9df;
  padding-top: 10px;
  white-space: pre-wrap;
}

@media (max-width: 1060px) {
  .reader-grid {
    grid-template-columns: 1fr;
  }

  .paragraph-list {
    max-height: none;
  }
}

@media (max-width: 720px) {
  .reader-view {
    padding: 20px 16px;
  }

  .reader-header,
  .translation-head {
    align-items: stretch;
    flex-direction: column;
  }

  .reader-meta {
    justify-content: flex-start;
  }

  .translation-actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
