<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { apiGet, apiPost } from "../api/client";
import StatusBadge from "../components/StatusBadge.vue";
import type { GlossaryTerm } from "../types";

const terms = ref<GlossaryTerm[]>([]);
const sourceTerm = ref("");
const targetTerm = ref("");
const note = ref("");
const keepEnglish = ref(false);
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const formError = ref("");

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

onMounted(loadTerms);
</script>

<template>
  <section class="glossary-view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Translation Memory</p>
        <h1>Glossary</h1>
      </div>
    </header>

    <form class="term-form" @submit.prevent="addTerm">
      <label>
        <span>Source term</span>
        <input v-model="sourceTerm" autocomplete="off" />
      </label>
      <label>
        <span>Target term</span>
        <input v-model="targetTerm" autocomplete="off" />
      </label>
      <label class="wide">
        <span>Note</span>
        <input v-model="note" autocomplete="off" />
      </label>
      <label class="checkbox-label">
        <input v-model="keepEnglish" type="checkbox" />
        <span>Keep English</span>
      </label>
      <button class="primary-button" type="submit" :disabled="saving || !canSave">
        {{ saving ? "Adding..." : "Add term" }}
      </button>
    </form>

    <p v-if="formError" class="alert">{{ formError }}</p>
    <p v-if="error" class="alert">{{ error }}</p>

    <div class="glossary-panel">
      <div class="table-head">
        <span>Source</span>
        <span>Target</span>
        <span>Note</span>
        <span>Status</span>
      </div>

      <p v-if="loading" class="muted-state">Loading glossary...</p>
      <p v-else-if="!terms.length" class="muted-state">
        No glossary terms yet. Add preferred translations for recurring technical terms.
      </p>

      <template v-else>
        <div v-for="term in terms" :key="term.id" class="term-row">
          <span class="strong-text">{{ term.source_term }}</span>
          <span>{{ term.target_term }}</span>
          <span class="note-text">{{ term.note || "No note" }}</span>
          <span class="status-cell">
            <StatusBadge :status="term.enabled ? 'enabled' : 'disabled'" />
            <span v-if="term.keep_english" class="mini-tag">EN</span>
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
}

.view-header {
  max-width: 1040px;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #63716a;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: #1f2a25;
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
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 16px;
  background: #fffdfa;
}

label {
  display: grid;
  gap: 7px;
  min-width: 0;
  color: #58615a;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

input {
  width: 100%;
  min-width: 0;
  border: 1px solid #d8d3c8;
  border-radius: 6px;
  padding: 10px 11px;
  background: #fbfaf7;
  color: #26332c;
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
  border: 1px solid #244c3d;
  border-radius: 6px;
  padding: 0 14px;
  background: #244c3d;
  color: #fffdfa;
  font-weight: 700;
}

.primary-button:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.alert {
  max-width: 1040px;
  margin: 0 0 12px;
  border: 1px solid #e4b5ae;
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff2ef;
  color: #8a3028;
}

.glossary-panel {
  max-width: 1040px;
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  overflow: hidden;
  background: #fffdfa;
}

.table-head,
.term-row {
  display: grid;
  grid-template-columns: minmax(140px, 1fr) minmax(140px, 1fr) minmax(160px, 1.2fr) 150px;
  align-items: center;
  gap: 16px;
}

.table-head {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e0d7;
  background: #f4f0e8;
  color: #5b635d;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.term-row {
  min-height: 52px;
  padding: 12px 16px;
  border-bottom: 1px solid #eee9df;
  color: #40473f;
}

.term-row:last-child {
  border-bottom: 0;
}

.strong-text {
  color: #1f2a25;
  font-weight: 700;
}

.note-text {
  min-width: 0;
  overflow: hidden;
  color: #62675f;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mini-tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  border-radius: 4px;
  padding: 0 7px;
  background: #ece7de;
  color: #5d554b;
  font-size: 12px;
  font-weight: 700;
}

.muted-state {
  margin: 0;
  padding: 28px 16px;
  color: #62675f;
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
