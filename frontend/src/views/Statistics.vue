<template>
  <section>
    <h2>Statistics</h2>
    <button @click="load">Refresh</button>
    <div v-if="loading">Loading…</div>
    <pre v-else>{{ stats }}</pre>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../services/api";
const stats = ref(null);
const loading = ref(false);
async function load() {
  loading.value = true;
  try {
    stats.value = await api.databaseStats();
  } catch (e) {
    alert(e.message);
  } finally {
    loading.value = false;
  }
}
load();
</script>
