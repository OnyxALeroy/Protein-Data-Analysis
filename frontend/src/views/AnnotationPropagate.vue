<template>
  <section>
    <h2>Label Propagation</h2>
    <form @submit.prevent="submit">
      <label
        >Attribute: <input v-model="attribute" placeholder="ec or go or custom"
      /></label>
      <label
        >Max iterations:
        <input v-model.number="max_iterations" type="number" value="100"
      /></label>
      <label
        >Threshold: <input v-model.number="threshold" step="0.001"
      /></label>
      <button type="submit">Run</button>
    </form>
    <div v-if="result">{{ result }}</div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../services/api";
const attribute = ref("ec");
const max_iterations = ref(100);
const threshold = ref(0.01);
const result = ref(null);

async function submit() {
  try {
    result.value = await api.propagate({
      attribute: attribute.value,
      max_iterations: max_iterations.value,
      threshold: threshold.value,
    });
  } catch (e) {
    alert(e.message);
  }
}
</script>
