<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { apiDelete, apiGet, apiPost } from "../api/client";
import StatusBadge from "../components/StatusBadge.vue";
import { useI18n } from "../i18n";
import type { GlossaryTerm } from "../types";
import { describeGlossaryDeleteError, removeGlossaryTerm } from "../utils/glossary";

const terms = ref<GlossaryTerm[]>([]);
const sourceTerm = ref("");
const targetTerm = ref("");
const note = ref("");
const keepEnglish = ref(false);
const loading = ref(true);
const saving = ref(false);
const deletingTermId = ref<number | null>(null);
const deleteErrors = ref<Record<number, string>>({});
const error = ref("");
const formError = ref("");
const { t } = useI18n();

const canSave = computed(() => sourceTerm.value.trim() !== "" && targetTerm.value.trim() !== "");

async function loadTerms() {
  loading.value = true;
  error.value = "";
  try {
    terms.value = await apiGet<GlossaryTerm[]>("/api/glossary");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load glossary";
  } finally {
    loading.value = false;
  }
}

async function addTerm() {
  if (!canSave.value) {
    formError.value = "Source and target terms are required.";
    return;
  }

  saving.value = true;
  formError.value = "";
  try {
    await apiPost<GlossaryTerm>("/api/glossary", {
      source_term: sourceTerm.value.trim(),
      target_term: targetTerm.value.trim(),
      note: note.value.trim(),
      keep_english: keepEnglish.value
    });
    sourceTerm.value = "";
    targetTerm.value = "";
    note.value = "";
    keepEnglish.value = false;
    await loadTerms();
  } catch (err) {
    formError.value = err instanceof Error ? err.message : "Failed to add glossary term";
  } finally {
    saving.value = false;
  }
}

async function deleteTerm(termId: number) {
  deletingTermId.value = termId;
  delete deleteErrors.value[termId];
  try {
    await apiDelete(`/api/glossary/${termId}`);
    terms.value = removeGlossaryTerm(terms.value, termId);
  } catch (err) {
    deleteErrors.value[termId] = describeGlossaryDeleteError(err);
  } finally {
    deletingTermId.value = null;
  }
}

onMounted(loadTerms);
</script>

<template>
  <section class="glossary-view">
    <header class="view-header">
      <div>
        <p class="eyebrow">{{ t("glossaryEyebrow") }}</p>
        <h1>{{ t("glossaryTitle") }}</h1>
      </div>
    </header>

    <form class="term-form" @submit.prevent="addTerm">
      <label>
        <span>{{ t("sourceTerm") }}</span>
        <input v-model="sourceTerm" autocomplete="off" />
      </label>
      <label>
        <span>{{ t("targetTerm") }}</span>
        <input v-model="targetTerm" autocomplete="off" />
      </label>
      <label class="wide">
        <span>{{ t("note") }}</span>
        <input v-model="note" autocomplete="off" />
      </label>
      <label class="checkbox-label">
        <input v-model="keepEnglish" type="checkbox" />
        <span>{{ t("keepEnglish") }}</span>
      </label>
      <button class="primary-button" type="submit" :disabled="saving || !canSave">
        {{ saving ? t("adding") : t("addTerm") }}
      </button>
    </form>

    <p v-if="formError" class="alert">{{ formError }}</p>
    <p v-if="error" class="alert">{{ error }}</p>

    <div class="glossary-panel">
      <div class="table-head">
        <span>{{ t("source") }}</span>
        <span>{{ t("target") }}</span>
        <span>{{ t("note") }}</span>
        <span>{{ t("tableStatus") }}</span>
        <span>Actions</span>
      </div>

      <p v-if="loading" class="muted-state">{{ t("loadingGlossary") }}</p>
      <p v-else-if="!terms.length" class="muted-state">
        {{ t("emptyGlossary") }}
      </p>

      <template v-else>
        <div v-for="term in terms" :key="term.id" class="term-row">
          <span class="strong-text">{{ term.source_term }}</span>
          <span>{{ term.target_term }}</span>
          <span class="note-text">{{ term.note || t("noNote") }}</span>
          <span class="status-cell">
            <StatusBadge :status="term.enabled ? 'enabled' : 'disabled'" />
            <span v-if="term.keep_english" class="mini-tag">EN</span>
          </span>
          <span class="action-cell">
            <button
              class="delete-button"
              type="button"
              :disabled="deletingTermId === term.id"
              @click="deleteTerm(term.id)"
            >
              {{ deletingTermId === term.id ? "Deleting..." : "Delete" }}
            </button>
            <small v-if="deleteErrors[term.id]" class="row-error">{{ deleteErrors[term.id] }}</small>
          </span>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.glossary-view {
  min-height: 100vh;
  padding: 32px;
  background: var(--app-bg);
}

.view-header {
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

.term-form {
  display: grid;
  grid-template-columns: minmax(160px, 1fr) minmax(160px, 1fr) minmax(200px, 1.2fr) auto auto;
  align-items: end;
  gap: 12px;
  max-width: 1040px;
  margin-bottom: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  background: var(--panel-bg);
}

label {
  display: grid;
  gap: 7px;
  min-width: 0;
  color: var(--muted-text);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

input {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 11px;
  background: var(--input-bg);
  color: var(--body-text);
  font-size: 14px;
  text-transform: none;
}

.checkbox-label {
  align-items: center;
  display: flex;
  gap: 8px;
  min-height: 40px;
  white-space: nowrap;
}

.checkbox-label input {
  width: 16px;
  height: 16px;
}

.primary-button {
  min-height: 40px;
  border: 1px solid var(--accent);
  border-radius: 6px;
  padding: 0 14px;
  background: var(--accent);
  color: var(--accent-contrast);
  font-weight: 700;
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
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

.glossary-panel {
  max-width: 1040px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--panel-bg);
}

.table-head,
.term-row {
  display: grid;
  grid-template-columns: minmax(140px, 1fr) minmax(140px, 1fr) minmax(160px, 1.2fr) 150px 108px;
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

.term-row {
  min-height: 52px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  color: var(--body-text);
}

.term-row:last-child {
  border-bottom: 0;
}

.strong-text {
  color: var(--strong-text);
  font-weight: 700;
}

.note-text {
  min-width: 0;
  overflow: hidden;
  color: var(--muted-text);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-cell {
  display: grid;
  justify-items: end;
  gap: 5px;
}

.row-error {
  max-width: 190px;
  color: var(--danger-text);
  font-size: 11px;
  line-height: 1.35;
  text-align: right;
}

.delete-button {
  min-height: 34px;
  border: 1px solid var(--danger-border);
  border-radius: 6px;
  padding: 0 10px;
  background: var(--danger-bg);
  color: var(--danger-text);
  font-weight: 700;
}

.delete-button:disabled {
  cursor: wait;
  opacity: 0.62;
}

.mini-tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  border-radius: 4px;
  padding: 0 7px;
  background: var(--panel-muted-bg);
  color: var(--muted-text);
  font-size: 12px;
  font-weight: 700;
}

.muted-state {
  margin: 0;
  padding: 28px 16px;
  color: var(--muted-text);
}

@media (max-width: 900px) {
  .term-form {
    grid-template-columns: 1fr 1fr;
  }

  .wide,
  .checkbox-label,
  .primary-button {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .glossary-view {
    padding: 20px 16px;
  }

  .term-form {
    grid-template-columns: 1fr;
  }

  .table-head {
    display: none;
  }

  .term-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }
}
</style>
