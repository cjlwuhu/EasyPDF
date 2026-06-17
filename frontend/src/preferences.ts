import { reactive, watch } from "vue";

export type Language = "zh" | "en";
export type ThemeMode = "light" | "dark";

export interface UserPreferences {
  language: Language;
  theme: ThemeMode;
}

const STORAGE_KEY = "easypdf.preferences";
const DEFAULT_PREFERENCES: UserPreferences = {
  language: "zh",
  theme: "light"
};

export const preferences = reactive<UserPreferences>(readPreferences());

watch(
  preferences,
  () => {
    writePreferences(preferences);
    applyTheme(preferences.theme);
  },
  { deep: true }
);

applyTheme(preferences.theme);

export function normalizePreferences(value: unknown): UserPreferences {
  const candidate = value as Partial<UserPreferences> | null;
  return {
    language: candidate?.language === "en" ? "en" : "zh",
    theme: candidate?.theme === "dark" ? "dark" : "light"
  };
}

export function displayLanguageName(language: Language): string {
  return language === "zh" ? "中文" : "English";
}

export function setLanguage(language: Language) {
  preferences.language = language;
}

export function setTheme(theme: ThemeMode) {
  preferences.theme = theme;
}

function readPreferences(): UserPreferences {
  if (typeof localStorage === "undefined") {
    return DEFAULT_PREFERENCES;
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? normalizePreferences(JSON.parse(raw)) : DEFAULT_PREFERENCES;
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

function writePreferences(value: UserPreferences) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
}

function applyTheme(theme: ThemeMode) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
}
