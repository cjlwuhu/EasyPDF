<script setup lang="ts">
import { ChevronDown, ChevronUp, Download, FileText, Languages, TextSelect } from "@lucide/vue";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiDownload, apiGet, apiPost } from "../api/client";
import PdfPane from "../components/PdfPane.vue";
import SelectionToolbar from "../components/SelectionToolbar.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { useI18n } from "../i18n";
import type { DocumentDetail, Paragraph, ParagraphStatus, TranslationJob } from "../types";
import {
  isParagraphInRange,
  hasTranslatedParagraphs,
  normalizeParagraphRange,
  normalizeVisiblePanels,
  sortParagraphsByReadingOrder,
  visiblePanels,
  type PanelVisibility,
  type ParagraphRange,
  type ReaderPanel
} from "../utils/readerWorkbench";
import { formatTranslationJobProgress } from "../utils/translationJob";

const route = useRoute();
const panelStorageKey = "easypdf.reader.panels";
const panelControls = [
  { panel: "pdf", label: "PDF 原文", icon: FileText },
  { panel: "source", label: "英文提取段落", icon: TextSelect },
  { panel: "translation", label: "中文译文", icon: Languages }
] as const;

function loadPanelVisibility(): PanelVisibility {
  try {
    return normalizeVisiblePanels(JSON.parse(window.localStorage.getItem(panelStorageKey) || "null"));
  } catch {
    return normalizeVisiblePanels(null);
  }
}

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
const rangeTranslationLoading = ref(false);
const rangeTranslationError = ref("");
const translationJob = ref<TranslationJob | null>(null);
const translationJobError = ref("");
const startTranslationLoading = ref(false);
const exportLoading = ref(false);
const exportError = ref("");
const pdfPageNumber = ref(1);
const rangeStartIndex = ref<number | null>(null);
const rangeEndIndex = ref<number | null>(null);
const readerGrid = ref<HTMLElement | null>(null);
const panelVisibility = ref<PanelVisibility>(loadPanelVisibility());
const inspectorOpen = ref(true);
const threePanelWeights = ref<Record<ReaderPanel, number>>({ pdf: 38, source: 38, translation: 24 });
const pairWeights = ref<[number, number]>([1, 1]);
const { t } = useI18n();
let translationPoller: number | undefined;
let activeResizeIndex: number | null = null;
let resizeStartX = 0;
let resizeStartWeights: number[] = [];

const documentId = computed(() => String(route.params.id));
const pdfUrl = computed(() => `/api/documents/${documentId.value}/file`);
const paragraphs = computed(() => documentDetail.value?.paragraphs ?? []);
const sortedParagraphs = computed(() => sortParagraphsByReadingOrder(paragraphs.value));
const selectedSourceText = computed(() => selectedParagraph.value?.source_text ?? "");
const selectedTranslationText = computed(
  () => selectedParagraph.value?.translated_text || "Translation pending"
);
const paragraphIndexById = computed(() => {
  const indexes = new Map<number, number>();
  sortedParagraphs.value.forEach((paragraph, index) => {
    indexes.set(paragraph.id, index);
  });
  return indexes;
});
const selectedParagraphIndex = computed(() =>
  selectedParagraph.value ? paragraphIndexById.value.get(selectedParagraph.value.id) ?? null : null
);
const selectedRange = computed<ParagraphRange | null>(() =>
  normalizeParagraphRange(rangeStartIndex.value, rangeEndIndex.value)
);
const rangeParagraphs = computed(() =>
  sortedParagraphs.value.filter((paragraph) =>
    isParagraphInRange(paragraphIndexById.value.get(paragraph.id) ?? -1, selectedRange.value)
  )
);
const visibleReaderPanels = computed(() => visiblePanels(panelVisibility.value));
const readerGridColumns = computed(() => {
  const panels = visibleReaderPanels.value;
  const weights = panels.length === 3
    ? panels.map((panel) => threePanelWeights.value[panel])
    : panels.length === 2
      ? pairWeights.value
      : [1];
  return weights.map((weight, index) => (
    `${index > 0 ? "8px " : ""}minmax(0, ${weight}fr)`
  )).join(" ");
});
const translationJobProgress = computed(() =>
  translationJob.value ? formatTranslationJobProgress(translationJob.value) : null
);
const hasTranslatableParagraphs = computed(() =>
  sortedParagraphs.value.some((paragraph) => paragraph.status === "pending" || paragraph.status === "failed")
);
const canExportTranslation = computed(() => hasTranslatedParagraphs(sortedParagraphs.value));

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

async function selectParagraph(paragraph: Paragraph) {
  selectedParagraph.value = paragraph;
  selectedText.value = paragraph.translated_text || paragraph.source_text;
  pdfPageNumber.value = paragraph.page_number;
  showOriginal.value = false;
  assistantAnswer.value = "";
  assistantError.value = "";
  retranslateError.value = "";
  rangeTranslationError.value = "";
  await nextTick();
  document.querySelectorAll<HTMLElement>(`[data-paragraph-id="${paragraph.id}"]`).forEach((element) => {
    element.scrollIntoView({ block: "nearest", behavior: "smooth" });
  });
}

async function retranslateParagraph(paragraph: Paragraph) {
  retranslateLoading.value = true;
  retranslateError.value = "";
  try {
    const result = await apiPost<{ paragraph_id: number; translated_text: string; status: string }>(
      "/api/translations/paragraph",
      { paragraph_id: paragraph.id }
    );
    paragraph.translated_text = result.translated_text;
    paragraph.status = result.status as ParagraphStatus;
    if (selectedParagraph.value?.id === paragraph.id) {
      selectedText.value = result.translated_text;
    }
  } catch (err) {
    retranslateError.value = err instanceof Error ? err.message : "Failed to retranslate paragraph";
  } finally {
    retranslateLoading.value = false;
  }
}

async function retranslateSelectedParagraph() {
  if (!selectedParagraph.value) return;
  await retranslateParagraph(selectedParagraph.value);
}

function setRangeStart() {
  rangeStartIndex.value = selectedParagraphIndex.value;
}

function setRangeEnd() {
  rangeEndIndex.value = selectedParagraphIndex.value;
}

async function translateSelectedRange() {
  if (!selectedRange.value || rangeParagraphs.value.length === 0) return;

  rangeTranslationLoading.value = true;
  rangeTranslationError.value = "";
  try {
    for (const paragraph of rangeParagraphs.value) {
      await retranslateParagraph(paragraph);
    }
  } catch (err) {
    rangeTranslationError.value = err instanceof Error ? err.message : "Failed to translate selected range";
  } finally {
    rangeTranslationLoading.value = false;
  }
}

function stopTranslationPolling() {
  if (translationPoller !== undefined) {
    window.clearInterval(translationPoller);
    translationPoller = undefined;
  }
}

function togglePanel(panel: ReaderPanel) {
  const panels = visibleReaderPanels.value;
  if (panelVisibility.value[panel] && panels.length === 1) return;
  panelVisibility.value = {
    ...panelVisibility.value,
    [panel]: !panelVisibility.value[panel]
  };
  pairWeights.value = [1, 1];
}

function handleResizeMove(event: PointerEvent) {
  if (activeResizeIndex === null || !readerGrid.value) return;

  const width = readerGrid.value.getBoundingClientRect().width;
  if (width <= 0) return;

  const totalWeight = resizeStartWeights.reduce((sum, value) => sum + value, 0);
  const deltaWeight = ((event.clientX - resizeStartX) / width) * totalWeight;
  const leftIndex = activeResizeIndex;
  const rightIndex = leftIndex + 1;
  const pairTotal = resizeStartWeights[leftIndex] + resizeStartWeights[rightIndex];
  const minimum = pairTotal * 0.2;
  const nextLeft = Math.min(Math.max(resizeStartWeights[leftIndex] + deltaWeight, minimum), pairTotal - minimum);
  const nextRight = pairTotal - nextLeft;

  if (visibleReaderPanels.value.length === 3) {
    const leftPanel = visibleReaderPanels.value[leftIndex];
    const rightPanel = visibleReaderPanels.value[rightIndex];
    threePanelWeights.value = {
      ...threePanelWeights.value,
      [leftPanel]: nextLeft,
      [rightPanel]: nextRight
    };
  } else {
    pairWeights.value = [nextLeft, nextRight];
  }
}

function stopResize() {
  activeResizeIndex = null;
  window.removeEventListener("pointermove", handleResizeMove);
  window.removeEventListener("pointerup", stopResize);
}

function startResize(splitterIndex: number, event: PointerEvent) {
  activeResizeIndex = splitterIndex;
  resizeStartX = event.clientX;
  resizeStartWeights = visibleReaderPanels.value.length === 3
    ? visibleReaderPanels.value.map((panel) => threePanelWeights.value[panel])
    : [...pairWeights.value];
  window.addEventListener("pointermove", handleResizeMove);
  window.addEventListener("pointerup", stopResize);
}

watch(panelVisibility, (visibility) => {
  window.localStorage.setItem(panelStorageKey, JSON.stringify(visibility));
}, { deep: true });

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

async function downloadTranslationDocx() {
  if (!canExportTranslation.value) return;

  exportLoading.value = true;
  exportError.value = "";
  try {
    const result = await apiDownload(`/api/documents/${documentId.value}/translation.docx`);
    const objectUrl = window.URL.createObjectURL(result.blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = result.filename;
    link.click();
    window.URL.revokeObjectURL(objectUrl);
  } catch (err) {
    exportError.value = err instanceof Error ? err.message : "Failed to export translation";
  } finally {
    exportLoading.value = false;
  }
}

onMounted(loadDocument);
onBeforeUnmount(() => {
  stopTranslationPolling();
  stopResize();
});
</script>

<template>
  <section class="reader-view">
    <header class="reader-header">
      <div>
        <p class="eyebrow">{{ t("readerEyebrow") }}</p>
        <h1>{{ documentDetail?.title || t("pdfReader") }}</h1>
      </div>
      <div class="reader-header-actions">
        <div class="reader-meta">
          <span>{{ documentDetail?.original_filename || `Document ${documentId}` }}</span>
          <StatusBadge v-if="documentDetail" :status="documentDetail.status" />
        </div>
        <div class="view-toolbar" role="toolbar" aria-label="阅读面板显示控制">
          <button
            v-for="control in panelControls"
            :key="control.panel"
            class="icon-button"
            :class="{ active: panelVisibility[control.panel] }"
            type="button"
            :title="`${panelVisibility[control.panel] ? '隐藏' : '显示'}${control.label}`"
            :aria-label="`${panelVisibility[control.panel] ? '隐藏' : '显示'}${control.label}`"
            :aria-pressed="panelVisibility[control.panel]"
            :disabled="panelVisibility[control.panel] && visibleReaderPanels.length === 1"
            @click="togglePanel(control.panel)"
          >
            <component :is="control.icon" :size="17" aria-hidden="true" />
          </button>
          <button
            class="icon-button"
            type="button"
            title="导出中文译文为 Word"
            aria-label="导出中文译文为 Word"
            :disabled="exportLoading || !canExportTranslation"
            @click="downloadTranslationDocx"
          >
            <Download :size="17" aria-hidden="true" />
          </button>
        </div>
      </div>
    </header>

    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="exportError" class="alert">{{ exportError }}</p>

    <div ref="readerGrid" class="reader-grid" :style="{ gridTemplateColumns: readerGridColumns }">
      <template v-for="(panel, panelIndex) in visibleReaderPanels" :key="panel">
        <aside v-if="panel === 'pdf'" class="reader-panel pdf-column" aria-label="PDF 原文">
          <PdfPane v-model:page-number="pdfPageNumber" :file-url="pdfUrl" />
        </aside>

        <main v-else-if="panel === 'source'" class="reader-panel content-column source-column" aria-label="英文提取段落">
          <div class="translation-head">
            <div>
              <p class="eyebrow">Extracted text</p>
              <h2>英文段落 · {{ sortedParagraphs.length }}</h2>
            </div>
            <div class="translation-actions">
              <button class="secondary-button" type="button" :disabled="selectedParagraphIndex === null" @click="setRangeStart">
                设为起点
              </button>
              <button class="secondary-button" type="button" :disabled="selectedParagraphIndex === null" @click="setRangeEnd">
                设为终点
              </button>
              <button class="primary-button" type="button" :disabled="rangeTranslationLoading || !selectedRange" @click="translateSelectedRange">
                {{ rangeTranslationLoading ? "翻译中..." : "翻译区间" }}
              </button>
            </div>
          </div>
          <p v-if="rangeTranslationError" class="alert compact">{{ rangeTranslationError }}</p>
          <p v-if="loading" class="muted-state">{{ t("loadingDocument") }}</p>
          <p v-else-if="!sortedParagraphs.length" class="muted-state">{{ t("noParagraphs") }}</p>
          <div v-else class="paragraph-list">
            <button
              v-for="paragraph in sortedParagraphs"
              :key="paragraph.id"
              :data-paragraph-id="paragraph.id"
              class="paragraph-card source-card"
              :class="{
                selected: selectedParagraph?.id === paragraph.id,
                'in-range': isParagraphInRange(paragraphIndexById.get(paragraph.id) ?? -1, selectedRange)
              }"
              type="button"
              @click="selectParagraph(paragraph)"
            >
              <span class="paragraph-meta">
                <span>Page {{ paragraph.page_number }} · #{{ paragraph.reading_order + 1 }}</span>
                <StatusBadge :status="paragraph.status" />
              </span>
              <span class="paragraph-text">{{ paragraph.source_text }}</span>
            </button>
          </div>
        </main>

        <main v-else class="reader-panel content-column translation-column" aria-label="中文译文">
          <div class="translation-head">
            <div>
              <p class="eyebrow">Translation</p>
              <h2>中文译文 · {{ sortedParagraphs.length }}</h2>
            </div>
            <div class="translation-actions">
              <button class="primary-button" type="button" :disabled="startTranslationLoading || !hasTranslatableParagraphs" @click="startDocumentTranslation">
                {{ startTranslationLoading ? t("starting") : t("generateTranslation") }}
              </button>
              <span v-if="selectedRange" class="selection-chip">范围 {{ selectedRange.start + 1 }}-{{ selectedRange.end + 1 }}</span>
            </div>
          </div>

          <div v-if="translationJobProgress" class="job-progress" aria-live="polite">
            <div class="progress-text">
              <span>{{ translationJobProgress.label }}</span>
              <span>{{ translationJobProgress.percent }}%</span>
            </div>
            <div class="progress-track"><span :style="{ width: `${translationJobProgress.percent}%` }"></span></div>
          </div>
          <p v-if="translationJobError" class="alert compact">{{ translationJobError }}</p>

          <section v-if="selectedParagraph" class="selection-panel">
            <button class="inspector-toggle" type="button" :aria-expanded="inspectorOpen" @click="inspectorOpen = !inspectorOpen">
              <span>
                <span class="panel-label">当前选段</span>
                Page {{ selectedParagraph.page_number }} · #{{ selectedParagraph.reading_order + 1 }}
              </span>
              <ChevronUp v-if="inspectorOpen" :size="17" aria-hidden="true" />
              <ChevronDown v-else :size="17" aria-hidden="true" />
            </button>

            <div v-if="inspectorOpen" class="inspector-body">
              <SelectionToolbar
                @show-original="showOriginal = !showOriginal"
                @retranslate="retranslateSelectedParagraph"
                @ask-ai="askAiAboutSelection"
              />
              <p v-if="retranslateLoading" class="muted-line">{{ t("retranslateParagraph") }}</p>
              <p v-if="retranslateError" class="alert compact">{{ retranslateError }}</p>
              <div v-if="showOriginal" class="detail-panel">
                <p class="panel-label">{{ t("original") }}</p>
                <p>{{ selectedSourceText }}</p>
              </div>
              <div class="detail-panel">
                <p class="panel-label">{{ t("selectedText") }}</p>
                <p>{{ selectedTranslationText }}</p>
              </div>
              <div class="detail-panel">
                <p class="panel-label">{{ t("askAi") }}</p>
                <textarea v-model="assistantQuestion" rows="3" :placeholder="t('askAiPlaceholder')"></textarea>
                <button class="primary-button" type="button" :disabled="assistantLoading" @click="askAiAboutSelection">
                  {{ assistantLoading ? t("asking") : t("ask") }}
                </button>
                <p v-if="assistantError" class="alert compact">{{ assistantError }}</p>
                <p v-if="assistantAnswer" class="assistant-answer">{{ assistantAnswer }}</p>
              </div>
            </div>
          </section>

          <p v-if="loading" class="muted-state">{{ t("loadingDocument") }}</p>
          <p v-else-if="!sortedParagraphs.length" class="muted-state">{{ t("noParagraphs") }}</p>
          <div v-else class="paragraph-list">
            <button
              v-for="paragraph in sortedParagraphs"
              :key="paragraph.id"
              :data-paragraph-id="paragraph.id"
              class="paragraph-card translation-card"
              :class="{ selected: selectedParagraph?.id === paragraph.id }"
              type="button"
              @click="selectParagraph(paragraph)"
            >
              <span class="paragraph-meta">
                <span>Page {{ paragraph.page_number }} · #{{ paragraph.reading_order + 1 }}</span>
                <StatusBadge :status="paragraph.status" />
              </span>
              <span class="paragraph-text" :class="{ pending: !paragraph.translated_text }">
                {{ paragraph.translated_text || "等待翻译" }}
              </span>
            </button>
          </div>
        </main>

        <button
          v-if="panelIndex < visibleReaderPanels.length - 1"
          class="pane-splitter"
          type="button"
          :aria-label="`调整${panelControls.find((item) => item.panel === panel)?.label || ''}面板宽度`"
          @pointerdown.prevent="startResize(panelIndex, $event)"
        ></button>
      </template>
    </div>
  </section>
</template>

<style scoped>
.reader-view {
  height: 100vh;
  padding: 28px;
  background: var(--app-bg);
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
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
  color: var(--muted-text);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1,
h2 {
  margin: 0;
  color: var(--strong-text);
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
  color: var(--muted-text);
}

.reader-header-actions {
  display: grid;
  justify-items: end;
  gap: 9px;
  min-width: 0;
}

.view-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.icon-button {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0;
  background: var(--input-bg);
  color: var(--muted-text);
}

.icon-button.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--strong-text);
}

.icon-button:hover,
.icon-button:focus-visible {
  border-color: var(--accent);
  outline: none;
}

.icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.reader-meta span:first-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-grid {
  display: grid;
  gap: 0;
  min-height: 0;
  align-items: stretch;
}

.reader-panel {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: 0 12px;
}

.content-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pane-splitter {
  width: 8px;
  min-width: 8px;
  border: 0;
  border-radius: 999px;
  padding: 0;
  background: linear-gradient(180deg, transparent, var(--border), transparent);
  cursor: col-resize;
}

.pane-splitter:hover,
.pane-splitter:focus-visible {
  background: var(--accent);
  outline: none;
}

.translation-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  background: var(--panel-bg);
}

.selection-chip {
  border-radius: 4px;
  padding: 5px 8px;
  background: var(--accent-soft);
  color: var(--strong-text);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.translation-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

.job-progress {
  display: grid;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  background: var(--panel-bg);
}

.progress-text {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--body-text);
  font-size: 13px;
  font-weight: 700;
}

.progress-track {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--panel-muted-bg);
}

.progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width 160ms ease;
}

.paragraph-list {
  display: grid;
  align-content: start;
  flex: 1;
  gap: 10px;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
}

.paragraph-card {
  display: grid;
  gap: 9px;
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  background: var(--panel-bg);
  color: var(--body-text);
  text-align: left;
}

.paragraph-card:hover,
.paragraph-card:focus-visible,
.paragraph-card.selected {
  border-color: var(--accent);
  background: var(--accent-soft);
  outline: none;
}

.paragraph-card.selected {
  box-shadow: inset 3px 0 0 var(--accent);
}

.paragraph-card.in-range {
  border-color: var(--accent);
  border-style: dashed;
}

.paragraph-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--muted-text);
  font-size: 12px;
  font-weight: 700;
}

.paragraph-text {
  color: var(--body-text);
  line-height: 1.7;
}

.paragraph-text.pending {
  color: var(--muted-text);
  font-style: italic;
}

.selection-panel,
.detail-panel {
  display: grid;
  gap: 10px;
}

.selection-panel {
  align-content: start;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--panel-bg);
}

.inspector-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  border: 0;
  padding: 11px 12px;
  background: var(--panel-muted-bg);
  color: var(--strong-text);
  text-align: left;
}

.inspector-toggle > span {
  display: grid;
  gap: 3px;
}

.inspector-body {
  display: grid;
  gap: 10px;
  max-height: 320px;
  overflow: auto;
  padding: 10px;
  border-top: 1px solid var(--border-soft);
}

.detail-panel {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  background: var(--panel-bg);
}

.detail-panel p {
  margin: 0;
  color: var(--body-text);
  line-height: 1.7;
}

.panel-label {
  color: var(--muted-text) !important;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

textarea {
  width: 100%;
  min-width: 0;
  resize: vertical;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 11px;
  background: var(--input-bg);
  color: var(--body-text);
  font-size: 14px;
  line-height: 1.5;
}

textarea:focus {
  border-color: var(--accent);
  outline: none;
}

.primary-button {
  justify-self: start;
  min-height: 36px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  padding: 0 14px;
  background: var(--accent);
  color: var(--accent-contrast);
  font-weight: 700;
}

.primary-button:disabled {
  cursor: wait;
  opacity: 0.68;
}

.secondary-button {
  min-height: 36px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0 12px;
  background: var(--input-bg);
  color: var(--strong-text);
  font-weight: 700;
}

.secondary-button:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.alert {
  margin: 0 0 12px;
  border: 1px solid var(--danger-border);
  border-radius: 6px;
  padding: 10px 12px;
  background: var(--danger-bg);
  color: var(--danger-text);
}

.compact {
  margin: 0;
}

.muted-state,
.muted-line {
  margin: 0;
  color: var(--muted-text);
}

.muted-state {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 28px 16px;
  background: var(--panel-bg);
}

.assistant-answer {
  border-top: 1px solid var(--border-soft);
  padding-top: 10px;
  white-space: pre-wrap;
}

@media (max-width: 1060px) {
  .reader-grid {
    grid-template-columns: 1fr !important;
    gap: 14px;
    overflow: auto;
  }

  .pane-splitter {
    display: none;
  }

  .pdf-column,
  .source-column,
  .translation-column {
    padding: 0;
    overflow: visible;
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

  .reader-header-actions {
    justify-items: start;
  }

  .translation-actions {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
