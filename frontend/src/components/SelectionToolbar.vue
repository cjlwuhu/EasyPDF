<script setup lang="ts">
defineEmits<{
  showOriginal: [];
  retranslate: [];
  askAi: [];
}>();
</script>

<template>
  <div class="selection-toolbar" role="toolbar" aria-label="Selected paragraph actions">
    <button type="button" @click="$emit('showOriginal')">Show original</button>
    <button type="button" @click="$emit('retranslate')">Retranslate</button>
    <button type="button" @click="$emit('askAi')">Ask AI</button>
  </div>
</template>

<style scoped>
.selection-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border: 1px solid #d8d3c8;
  border-radius: 8px;
  padding: 10px;
  background: #fffdfa;
  box-shadow: 0 10px 28px rgb(54 50 43 / 10%);
}

button {
  min-height: 34px;
  border: 1px solid #cfc8ba;
  border-radius: 6px;
  padding: 0 11px;
  background: #f7f3eb;
  color: #26332c;
  font-size: 13px;
  font-weight: 700;
}

button:hover,
button:focus-visible {
  border-color: #244c3d;
  background: #e9f1ec;
  outline: none;
}
</style>
