<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { apiGet, apiPost } from "../api/client";
import { displayLanguageName, preferences, setLanguage, setTheme, type Language, type ThemeMode } from "../preferences";
import { useI18n } from "../i18n";

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
const saving = ref(false);
const testingConnection = ref(false);
const error = ref("");
const saveMessage = ref("");
const connectionMessage = ref("");
const connectionOk = ref(false);
const apiKey = ref("");
const baseUrl = ref("");
const modelName = ref("");
const { t } = useI18n();

const databaseAddress = computed(() => {
  if (!settings.value) return "";
  const host = settings.value.mysql_host;
  const port = settings.value.mysql_port;
  const database = settings.value.mysql_database;

  if (!host && !port && !database) return "";
  return `${host ?? "unknown"}:${port ?? "unknown"}/${database ?? "unknown"}`;
});

function valueOrFallback(value: string | number | undefined) {
  if (value === undefined || value === "") return t("notExposed");
  return String(value);
}

async function loadSettings() {
  loading.value = true;
  error.value = "";
  try {
    settings.value = await apiGet<PublicSettings>("/api/settings");
    apiKey.value = "";
    baseUrl.value = settings.value.base_url;
    modelName.value = settings.value.model_name;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load settings";
  } finally {
    loading.value = false;
  }
}

async function saveSettings() {
  saving.value = true;
  error.value = "";
  saveMessage.value = "";
  connectionMessage.value = "";
  try {
    settings.value = await apiPost<PublicSettings>("/api/settings", {
      api_key: apiKey.value,
      base_url: baseUrl.value,
      model_name: modelName.value
    });
    apiKey.value = "";
    baseUrl.value = settings.value.base_url;
    modelName.value = settings.value.model_name;
    saveMessage.value = t("saved");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to save settings";
  } finally {
    saving.value = false;
  }
}

async function testConnection() {
  testingConnection.value = true;
  error.value = "";
  saveMessage.value = "";
  connectionMessage.value = "";
  connectionOk.value = false;
  try {
    const result = await apiPost<{ ok: boolean; message: string }>("/api/settings/test-ai", {
      api_key: apiKey.value,
      base_url: baseUrl.value,
      model_name: modelName.value
    });
    connectionOk.value = result.ok;
    connectionMessage.value = result.ok ? t("connectionSucceeded") : result.message;
  } catch (err) {
    connectionOk.value = false;
    connectionMessage.value = err instanceof Error ? err.message : "Failed to test API connection";
  } finally {
    testingConnection.value = false;
  }
}

onMounted(loadSettings);
</script>

<template>
  <section class="settings-view">
    <header class="view-header">
      <p class="eyebrow">{{ t("settingsEyebrow") }}</p>
      <h1>{{ t("settingsTitle") }}</h1>
    </header>

    <p v-if="error" class="alert">{{ error }}</p>
    <p v-if="saveMessage" class="success">{{ saveMessage }}</p>
    <p v-if="connectionMessage" :class="connectionOk ? 'success' : 'alert'">{{ connectionMessage }}</p>
    <p v-if="loading" class="muted-state">Loading settings...</p>

    <div v-else-if="settings" class="settings-layout">
      <form class="settings-panel primary-panel" @submit.prevent="saveSettings">
        <div class="panel-heading">
          <p class="eyebrow">{{ t("aiSettings") }}</p>
          <h2>{{ t("apiKey") }} / {{ t("baseUrl") }} / {{ t("modelName") }}</h2>
        </div>
        <label class="wide">
          <span>{{ t("apiKey") }}</span>
          <input
            v-model="apiKey"
            type="password"
            autocomplete="off"
            :placeholder="settings.api_key_masked || t('apiKeyPlaceholder')"
          />
        </label>
        <label>
          <span>{{ t("baseUrl") }}</span>
          <input v-model="baseUrl" autocomplete="off" placeholder="https://api.openai.com/v1" />
        </label>
        <label>
          <span>{{ t("modelName") }}</span>
          <input v-model="modelName" autocomplete="off" placeholder="gpt-4.1-mini" />
        </label>
        <div class="button-row">
          <button class="primary-button" type="submit" :disabled="saving || testingConnection">
            {{ saving ? t("saving") : t("saveSettings") }}
          </button>
          <button
            class="secondary-button"
            type="button"
            :disabled="saving || testingConnection"
            @click="testConnection"
          >
            {{ testingConnection ? t("testingConnection") : t("testConnection") }}
          </button>
        </div>
      </form>

      <div class="settings-panel preference-panel">
        <div class="panel-heading">
          <p class="eyebrow">{{ t("appearance") }}</p>
          <h2>{{ t("theme") }} / {{ t("language") }}</h2>
        </div>
        <label>
          <span>{{ t("theme") }}</span>
          <select
            :value="preferences.theme"
            @change="setTheme(($event.target as HTMLSelectElement).value as ThemeMode)"
          >
            <option value="light">{{ t("lightMode") }}</option>
            <option value="dark">{{ t("darkMode") }}</option>
          </select>
        </label>
        <label>
          <span>{{ t("language") }}</span>
          <select
            :value="preferences.language"
            @change="setLanguage(($event.target as HTMLSelectElement).value as Language)"
          >
            <option value="zh">{{ displayLanguageName("zh") }}</option>
            <option value="en">{{ displayLanguageName("en") }}</option>
          </select>
        </label>
      </div>

      <div class="settings-panel runtime-panel">
        <div class="panel-heading">
          <p class="eyebrow">{{ t("systemInfo") }}</p>
          <h2>{{ t("mysql") }}</h2>
        </div>
      <label>
        <span>{{ t("mysql") }}</span>
        <input :value="databaseAddress || t('notExposed')" disabled />
      </label>
      <label>
        <span>{{ t("storageDirectory") }}</span>
        <input :value="valueOrFallback(settings.storage_dir)" disabled />
      </label>
      <label>
        <span>{{ t("translationConcurrency") }}</span>
        <input :value="valueOrFallback(settings.translation_concurrency)" disabled />
      </label>
      </div>
    </div>
  </section>
</template>

<style scoped>
.settings-view {
  min-height: 100vh;
  padding: 32px;
  background: var(--app-bg);
}

.view-header {
  max-width: 960px;
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

.settings-layout {
  display: grid;
  gap: 16px;
  max-width: 980px;
}

.settings-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 18px;
  background: var(--panel-bg);
}

.panel-heading,
.wide,
.button-row {
  grid-column: 1 / -1;
}

.panel-heading {
  display: grid;
  gap: 4px;
}

.panel-heading h2 {
  margin: 0;
  color: var(--strong-text);
  font-size: 18px;
  line-height: 1.25;
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

input,
select {
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

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.primary-button,
.secondary-button {
  min-height: 40px;
  border-radius: 6px;
  padding: 0 16px;
  font-weight: 700;
}

.primary-button {
  border: 1px solid var(--accent);
  background: var(--accent);
  color: var(--accent-contrast);
}

.secondary-button {
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--body-text);
}

.primary-button:disabled,
.secondary-button:disabled {
  cursor: wait;
  opacity: 0.68;
}

.alert {
  max-width: 960px;
  margin: 0 0 12px;
  border: 1px solid var(--danger-border);
  border-radius: 6px;
  padding: 10px 12px;
  background: var(--danger-bg);
  color: var(--danger-text);
}

.success {
  max-width: 960px;
  margin: 0 0 12px;
  border: 1px solid var(--success-border);
  border-radius: 6px;
  padding: 10px 12px;
  background: var(--success-bg);
  color: var(--success-text);
}

.muted-state {
  max-width: 960px;
  margin: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 24px;
  background: var(--panel-bg);
  color: var(--muted-text);
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
