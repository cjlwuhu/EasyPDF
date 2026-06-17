<script setup lang="ts">
defineProps<{ status: string }>();
</script>

<template>
  <span class="badge" :data-status="status">{{ status }}</span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  height: 24px;
  padding: 0 8px;
  border-radius: 4px;
  background: var(--panel-muted-bg);
  color: var(--body-text);
  font-size: 12px;
  font-weight: 650;
  line-height: 1;
  white-space: nowrap;
}

.badge[data-status="failed"] {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.badge[data-status="translated"],
.badge[data-status="corrected"] {
  background: var(--success-bg);
  color: var(--success-text);
}

.badge[data-status="translating"] {
  background: var(--accent-soft);
  color: var(--strong-text);
}
</style>
