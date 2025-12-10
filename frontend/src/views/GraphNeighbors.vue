<template>
  <section>
    <h2>Neighbors for {{ proteinId }}</h2>
    <div>
      <label
        >Depth: <input v-model.number="depth" type="number" min="1"
      /></label>
      <button @click="load">Load</button>
    </div>
    <div v-if="loading">Loading…</div>
    <ul v-else>
      <li v-for="n in neighbors" :key="n.id">
        {{ n.id }} — {{ n.name }} (dist: {{ n.distance }})
      </li>
    </ul>
  </section>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { api } from "../services/api";
import { useRoute } from "vue-router";

const route = useRoute();
const proteinId = route.params.proteinId;
const depth = ref(1);
const neighbors = ref([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  neighbors.value = await api.graphNeighbors(proteinId, depth.value);
  loading.value = false;
}

onMounted(load);
</script>
