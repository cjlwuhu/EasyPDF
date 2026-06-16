<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();
</script>

<template>
  <section class="placeholder-view">
    <div class="placeholder-panel">
      <h1>阅读器</h1>
      <p>Reader placeholder for document {{ route.params.id }}.</p>
    </div>
  </section>
</template>
