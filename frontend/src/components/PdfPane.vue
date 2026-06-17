<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import { GlobalWorkerOptions, getDocument, type PDFDocumentProxy } from "pdfjs-dist";

import { useI18n } from "../i18n";

const props = defineProps<{ fileUrl: string }>();
const { t } = useI18n();

GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.mjs", import.meta.url).toString();

const canvas = ref<HTMLCanvasElement | null>(null);
const loading = ref(false);
const error = ref("");
let renderToken = 0;
let pdfDocument: PDFDocumentProxy | null = null;

async function renderFirstPage(fileUrl: string) {
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
    pdfDocument?.destroy();
    pdfDocument = await getDocument(fileUrl).promise;
    if (token !== renderToken) return;

    const page = await pdfDocument.getPage(1);
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

watch(() => props.fileUrl, renderFirstPage, { immediate: true });

onBeforeUnmount(() => {
  renderToken += 1;
  pdfDocument?.destroy();
});
</script>

<template>
  <div class="pdf-pane">
    <div class="canvas-frame">
      <canvas ref="canvas" aria-label="PDF first page preview"></canvas>
      <p v-if="loading" class="pane-state">{{ t("loadingPdf") }}</p>
      <p v-if="error" class="pane-state error">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.pdf-pane {
  min-height: 0;
}

.canvas-frame {
  position: relative;
  min-height: 460px;
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
