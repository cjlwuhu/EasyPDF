<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import { GlobalWorkerOptions, getDocument, type PDFDocumentProxy } from "pdfjs-dist";

import { useI18n } from "../i18n";
import { clampPageNumber } from "../utils/readerWorkbench";

const props = defineProps<{ fileUrl: string; pageNumber: number }>();
const emit = defineEmits<{
  "update:pageNumber": [pageNumber: number];
}>();
const { t } = useI18n();

GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.mjs", import.meta.url).toString();

const canvas = ref<HTMLCanvasElement | null>(null);
const loading = ref(false);
const error = ref("");
const currentPage = ref(1);
const totalPages = ref(1);
let renderToken = 0;
let pdfDocument: PDFDocumentProxy | null = null;
let loadedFileUrl = "";

async function renderRequestedPage(fileUrl: string, requestedPage: number) {
  const token = ++renderToken;
  loading.value = true;
  error.value = "";

  await nextTick();
  const targetCanvas = canvas.value;
  if (!targetCanvas || !fileUrl) {
    loading.value = false;
    return;
  }

  try {
    if (!pdfDocument || loadedFileUrl !== fileUrl) {
      pdfDocument?.destroy();
      pdfDocument = await getDocument(fileUrl).promise;
      loadedFileUrl = fileUrl;
      totalPages.value = pdfDocument.numPages;
    }
    if (token !== renderToken) return;

    const safePage = clampPageNumber(requestedPage, totalPages.value);
    if (safePage !== requestedPage) {
      emit("update:pageNumber", safePage);
    }

    currentPage.value = safePage;
    const page = await pdfDocument.getPage(safePage);
    const viewport = page.getViewport({ scale: 1.25 });
    const context = targetCanvas.getContext("2d");
    if (!context) {
      throw new Error("Canvas rendering is unavailable");
    }

    targetCanvas.width = Math.floor(viewport.width);
    targetCanvas.height = Math.floor(viewport.height);
    targetCanvas.style.width = "100%";
    targetCanvas.style.height = "auto";

    await page.render({ canvasContext: context, viewport }).promise;
  } catch (err) {
    if (token === renderToken) {
      error.value = err instanceof Error ? err.message : "Failed to render PDF";
    }
  } finally {
    if (token === renderToken) {
      loading.value = false;
    }
  }
}

function goToPage(pageNumber: number) {
  emit("update:pageNumber", clampPageNumber(pageNumber, totalPages.value));
}

watch(() => [props.fileUrl, props.pageNumber] as const, ([fileUrl, pageNumber]) => {
  void renderRequestedPage(fileUrl, pageNumber);
}, { immediate: true });

onBeforeUnmount(() => {
  renderToken += 1;
  pdfDocument?.destroy();
});
</script>

<template>
  <div class="pdf-pane">
    <div class="pdf-toolbar">
      <button type="button" :disabled="loading || currentPage <= 1" aria-label="Previous PDF page" @click="goToPage(currentPage - 1)">
        ‹
      </button>
      <span>Page {{ currentPage }} / {{ totalPages }}</span>
      <button type="button" :disabled="loading || currentPage >= totalPages" aria-label="Next PDF page" @click="goToPage(currentPage + 1)">
        ›
      </button>
    </div>
    <div class="canvas-frame">
      <canvas ref="canvas" aria-label="PDF page preview"></canvas>
      <p v-if="loading" class="pane-state">{{ t("loadingPdf") }}</p>
      <p v-if="error" class="pane-state error">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.pdf-pane {
  min-height: 0;
  display: grid;
  gap: 10px;
}

.pdf-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  background: var(--panel-bg);
  color: var(--body-text);
  font-size: 13px;
  font-weight: 700;
}

.pdf-toolbar button {
  width: 32px;
  height: 30px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--input-bg);
  color: var(--strong-text);
  font-size: 18px;
  line-height: 1;
}

.pdf-toolbar button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.canvas-frame {
  position: relative;
  min-height: 0;
  height: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 18px;
  overflow: auto;
  background: var(--panel-muted-bg);
}

canvas {
  display: block;
  max-width: 100%;
  margin: 0 auto;
  background: #fff;
  box-shadow: 0 14px 34px rgb(40 35 28 / 16%);
}

.pane-state {
  position: absolute;
  top: 18px;
  left: 18px;
  margin: 0;
  border-radius: 6px;
  padding: 8px 10px;
  background: var(--panel-bg);
  color: var(--muted-text);
  font-size: 13px;
}

.error {
  color: var(--danger-text);
}
</style>
