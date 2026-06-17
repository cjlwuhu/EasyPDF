<script setup lang="ts">
import { useI18n } from "../i18n";

const { t } = useI18n();
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Primary navigation">
      <RouterLink class="brand" to="/">EasyPDF</RouterLink>
      <nav>
        <RouterLink to="/">{{ t("navLibrary") }}</RouterLink>
        <RouterLink to="/glossary">{{ t("navGlossary") }}</RouterLink>
        <RouterLink to="/settings">{{ t("navSettings") }}</RouterLink>
      </nav>
    </aside>
    <main class="workspace">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  background: var(--app-bg);
  color: var(--body-text);
}

.sidebar {
  border-right: 1px solid var(--border);
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: var(--sidebar-bg);
}

.brand {
  color: var(--strong-text);
  font-size: 22px;
  font-weight: 760;
  line-height: 1;
  text-decoration: none;
}

nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

nav a {
  color: var(--soft-text);
  padding: 10px 12px;
  border-radius: 6px;
  text-decoration: none;
}

nav a.router-link-active {
  background: var(--accent-soft);
  color: var(--strong-text);
}

.workspace {
  min-width: 0;
}

@media (max-width: 720px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: 0;
    border-bottom: 1px solid var(--border);
    padding: 16px;
  }

  nav {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>
