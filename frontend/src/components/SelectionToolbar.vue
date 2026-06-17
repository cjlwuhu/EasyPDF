<script setup lang="ts">
import { useI18n } from "../i18n";

defineEmits<{
  showOriginal: [];
  retranslate: [];
  askAi: [];
}>();

const { t } = useI18n();
</script>

<template>
  <div class="selection-toolbar" role="toolbar" aria-label="Selected paragraph actions">
    <button type="button" @click="$emit('showOriginal')">{{ t("showOriginal") }}</button>
    <button type="button" @click="$emit('retranslate')">{{ t("retranslate") }}</button>
    <button type="button" @click="$emit('askAi')">{{ t("askAi") }}</button>
  </div>
</template>

<style scoped>
.selection-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
  background: var(--panel-bg);
  box-shadow: 0 10px 28px rgb(54 50 43 / 10%);
}

button {
  min-height: 34px;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0 11px;
  background: var(--input-bg);
  color: var(--body-text);
  font-size: 13px;
  font-weight: 700;
}

button:hover,
button:focus-visible {
  border-color: var(--accent);
  background: var(--accent-soft);
  outline: none;
}
</style>
