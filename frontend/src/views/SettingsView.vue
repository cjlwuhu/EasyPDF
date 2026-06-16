<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { apiGet } from "../api/client";

interface PublicSettings {
  api_key_masked: string;
  base_url: string;
  model_name: string;
  mysql_host?: string;
  mysql_port?: number;
  mysql_database?: string;
  storage_dir?: string;
  translation_concurrency?: number;
}

const settings = ref<PublicSettings | null>(null);
const loading = ref(true);
const error = ref("");

const databaseAddress = computed(() => {
  if (!settings.value) return "";
  const host = settings.value.mysql_host;
  const port = settings.value.mysql_port;
  const database = settings.value.mysql_database;

  if (!host && !port && !database) return "";
  return `${host ?? "unknown"}:${port ?? "unknown"}/${database ?? "unknown"}`;
});

function valueOrFallback(value: string | number | undefined) {
  if (value === undefined || value === "") return "Not exposed";
  return String(value);
}

async function loadSettings() {
  loading.value = true;
  error.value = "";
  try {
    settings.value = await apiGet<PublicSettings>("/api/settings");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load settings";
  } finally {
    loading.value = false;
  }
}

onMounted(loadSettings);
</script>

<template>
  <section class="settings-view">
    <header class="view-header">
      <p class="eyebrow">Runtime</p>
      <h1>Settings</h1>
    </header>

    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="loading" class="muted-state">Loading settings...</p>

    <div v-else-if="settings" class="settings-panel">
      <label>
        <span>API key</span>
        <input :value="settings.api_key_masked" disabled />
      </label>
      <label>
        <span>Base URL</span>
        <input :value="settings.base_url" disabled />
      </label>
      <label>
        <span>Model</span>
        <input :value="settings.model_name" disabled />
      </label>
      <label>
        <span>MySQL</span>
        <input :value="databaseAddress || 'Not exposed'" disabled />
      </label>
      <label>
        <span>Storage directory</span>
        <input :value="valueOrFallback(settings.storage_dir)" disabled />
      </label>
      <label>
        <span>Translation concurrency</span>
        <input :value="valueOrFallback(settings.translation_concurrency)" disabled />
      </label>
    </div>
  </section>
</template>

<style scoped>
.settings-view {
  min-height: 100vh;
  padding: 32px;
}

.view-header {
  max-width: 960px;
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

.settings-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  max-width: 960px;
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 18px;
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
  background: #f8f6f1;
  color: #26332c;
  font-size: 14px;
  text-transform: none;
}

.alert {
  max-width: 960px;
  margin: 0 0 12px;
  border: 1px solid #e4b5ae;
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff2ef;
  color: #8a3028;
}

.muted-state {
  max-width: 960px;
  margin: 0;
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 24px;
  background: #fffdfa;
  color: #62675f;
}

@media (max-width: 760px) {
  .settings-view {
    padding: 20px 16px;
  }

  .settings-panel {
    grid-template-columns: 1fr;
  }
}
</style>
