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
  background: #e9e4da;
  color: #4a453d;
  font-size: 12px;
  font-weight: 650;
  line-height: 1;
  white-space: nowrap;
}

.badge[data-status="failed"] {
  background: #f2d7d5;
  color: #8a3028;
}

.badge[data-status="translated"],
.badge[data-status="corrected"] {
  background: #dce9e1;
  color: #28533c;
}

.badge[data-status="translating"] {
  background: #d8e6ef;
  color: #254d63;
}
</style>
