<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Primary navigation">
      <RouterLink class="brand" to="/">EasyPDF</RouterLink>
      <nav>
        <RouterLink to="/">文档库</RouterLink>
        <RouterLink to="/glossary">术语表</RouterLink>
        <RouterLink to="/settings">设置</RouterLink>
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
  background: #f6f4ef;
  color: #20231f;
}

.sidebar {
  border-right: 1px solid #d8d3c8;
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #fbfaf7;
}

.brand {
  color: #1f2a25;
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
  color: #36514a;
  padding: 10px 12px;
  border-radius: 6px;
  text-decoration: none;
}

nav a.router-link-active {
  background: #e2ebe6;
  color: #18382f;
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
    border-bottom: 1px solid #d8d3c8;
    padding: 16px;
  }

  nav {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>
