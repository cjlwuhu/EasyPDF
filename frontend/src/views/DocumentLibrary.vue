<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { apiGet, apiUpload } from "../api/client";
import StatusBadge from "../components/StatusBadge.vue";
import { useI18n } from "../i18n";
import type { DocumentSummary } from "../types";

const router = useRouter();
const documents = ref<DocumentSummary[]>([]);
const loading = ref(true);
const uploadInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const error = ref("");
const uploadError = ref("");
const { t } = useI18n();

const sortedDocuments = computed(() =>
  [...documents.value].sort((left, right) => right.id - left.id)
);

async function loadDocuments() {
  loading.value = true;
  error.value = "";
  try {
    documents.value = await apiGet<DocumentSummary[]>("/api/documents");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load documents";
  } finally {
    loading.value = false;
  }
}

function chooseFile() {
  uploadInput.value?.click();
}

async function uploadDocument(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";

  if (!file) return;
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    uploadError.value = "Only PDF files can be uploaded.";
    return;
  }

  uploading.value = true;
  uploadError.value = "";
  try {
    const document = await apiUpload<DocumentSummary>("/api/documents", file);
    await loadDocuments();
    await router.push(`/documents/${document.id}`);
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : "Failed to upload PDF";
  } finally {
    uploading.value = false;
  }
}

onMounted(loadDocuments);
</script>

<template>
  <section class="library-view">
    <header class="view-header">
      <div>
        <p class="eyebrow">{{ t("documentLibraryEyebrow") }}</p>
        <h1>{{ t("documentLibraryTitle") }}</h1>
      </div>
      <div class="upload-actions">
        <input
          ref="uploadInput"
          class="file-input"
          type="file"
          accept="application/pdf,.pdf"
          @change="uploadDocument"
        />
        <button class="primary-button" type="button" :disabled="uploading" @click="chooseFile">
          {{ uploading ? t("uploading") : t("uploadPdf") }}
        </button>
      </div>
    </header>

    <p v-if="uploadError" class="alert">{{ uploadError }}</p>
    <p v-if="error" class="alert">{{ error }}</p>

    <div class="library-panel">
      <div class="table-head">
        <span>{{ t("tableTitle") }}</span>
        <span>{{ t("tableFile") }}</span>
        <span>{{ t("tableStatus") }}</span>
      </div>

      <p v-if="loading" class="muted-state">{{ t("loadingDocuments") }}</p>
      <p v-else-if="!sortedDocuments.length" class="muted-state">
        {{ t("emptyDocuments") }}
      </p>

      <template v-else>
        <button
          v-for="document in sortedDocuments"
          :key="document.id"
          class="document-row"
          type="button"
          @click="router.push(`/documents/${document.id}`)"
        >
          <span class="document-title">{{ document.title }}</span>
          <span class="document-file">{{ document.original_filename }}</span>
          <StatusBadge :status="document.status" />
        </button>
      </template>
    </div>
  </section>
</template>

<style scoped>
.library-view {
  min-height: 100vh;
  padding: 32px;
  background: var(--app-bg);
}

.view-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  max-width: 1040px;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 6px;
  color: var(--muted-text);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: var(--strong-text);
  font-size: 30px;
  line-height: 1.2;
}

.upload-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-input {
  display: none;
}

.primary-button {
  min-height: 38px;
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

.alert {
  max-width: 1040px;
  margin: 0 0 12px;
  border: 1px solid var(--danger-border);
  border-radius: 6px;
  padding: 10px 12px;
  background: var(--danger-bg);
  color: var(--danger-text);
}

.library-panel {
  max-width: 1040px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--panel-bg);
}

.table-head,
.document-row {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) minmax(160px, 1fr) 120px;
  align-items: center;
  gap: 16px;
}

.table-head {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  background: var(--panel-muted-bg);
  color: var(--muted-text);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.document-row {
  width: 100%;
  border: 0;
  border-bottom: 1px solid var(--border-soft);
  padding: 14px 16px;
  background: transparent;
  color: inherit;
  text-align: left;
}

.document-row:last-child {
  border-bottom: 0;
}

.document-row:hover,
.document-row:focus-visible {
  background: var(--accent-soft);
  outline: none;
}

.document-title {
  min-width: 0;
  overflow: hidden;
  color: var(--strong-text);
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-file {
  min-width: 0;
  overflow: hidden;
  color: var(--muted-text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.muted-state {
  margin: 0;
  padding: 28px 16px;
  color: var(--muted-text);
}

@media (max-width: 760px) {
  .library-view {
    padding: 20px 16px;
  }

  .view-header {
    align-items: stretch;
    flex-direction: column;
  }

  .upload-actions,
  .primary-button {
    width: 100%;
  }

  .primary-button {
    justify-content: center;
  }

  .table-head {
    display: none;
  }

  .document-row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .document-file {
    grid-column: 1 / -1;
  }
}
</style>
