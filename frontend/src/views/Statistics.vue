<template>
  <section>
    <h2>Statistics</h2>
    <button @click="load">Refresh</button>
    <div v-if="loading">Loading…</div>
    <table v-else-if="stats" class="stats-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Total Proteins</td>
          <td>{{ stats.total_proteins.toLocaleString() }}</td>
        </tr>
        <tr>
          <td>Reviewed Proteins</td>
          <td>{{ stats.reviewed_proteins.toLocaleString() }}</td>
        </tr>
        <tr>
          <td>Unreviewed Proteins</td>
          <td>{{ stats.unreviewed_proteins.toLocaleString() }}</td>
        </tr>
        <tr>
          <td>Proteins with EC Numbers</td>
          <td>{{ stats.proteins_with_ec.toLocaleString() }}</td>
        </tr>
        <tr>
          <td>Proteins with GO Terms</td>
          <td>{{ stats.proteins_with_go.toLocaleString() }}</td>
        </tr>
        <tr>
          <td>Proteins with Domains</td>
          <td>{{ stats.proteins_with_domains.toLocaleString() }}</td>
        </tr>
        <tr>
          <td>Total Domains</td>
          <td>{{ stats.total_domains.toLocaleString() }}</td>
        </tr>
        <tr>
          <td>Total Annotations</td>
          <td>{{ stats.total_annotations.toLocaleString() }}</td>
        </tr>
      </tbody>
    </table>
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

<style scoped>
.stats-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.stats-table th,
.stats-table td {
  padding: 1rem 1.5rem;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.stats-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #495057;
  text-transform: uppercase;
  font-size: 0.875rem;
  letter-spacing: 0.5px;
}

.stats-table tbody tr:hover {
  background: #f8f9fa;
}

.stats-table tbody tr:last-child td {
  border-bottom: none;
}

.stats-table td:last-child {
  font-weight: bold;
  color: #007bff;
  font-size: 1.1rem;
}
</style>
