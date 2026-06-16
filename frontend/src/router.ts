import { createRouter, createWebHistory } from "vue-router";

const DocumentLibrary = () => import("./views/DocumentLibrary.vue");
const ReaderView = () => import("./views/ReaderView.vue");
const SettingsView = () => import("./views/SettingsView.vue");
const GlossaryView = () => import("./views/GlossaryView.vue");

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: DocumentLibrary },
    { path: "/documents/:id", component: ReaderView },
    { path: "/settings", component: SettingsView },
    { path: "/glossary", component: GlossaryView }
  ]
});
