<template>
  <section>
    <h2>Build Protein Graph</h2>
    <div>
      <label
        >Min similarity:
        <input
          v-model.number="min_similarity"
          type="number"
          step="0.01"
          min="0"
          max="1"
      /></label>
      <label
        >Max proteins: <input v-model.number="max_proteins" type="number"
      /></label>
      <button @click="build" :disabled="running">Build</button>
    </div>
    <div v-if="running">Building graph…</div>
    <div v-if="result">{{ result.message || JSON.stringify(result) }}</div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../services/api";

const min_similarity = ref(0.1);
const max_proteins = ref(10000);
const running = ref(false);
const result = ref(null);

async function build() {
  running.value = true;
  try {
    result.value = await api.buildGraph({
      min_similarity: min_similarity.value,
      max_proteins: max_proteins.value,
    });
  } catch (e) {
    alert("Build failed: " + e.message);
  } finally {
    running.value = false;
  }
}
</script>
