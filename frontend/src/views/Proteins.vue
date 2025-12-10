<template>
  <section>
    <h2>Proteins</h2>
    <div class="controls">
      <input
        v-model="query"
        @keyup.enter="search"
        placeholder="Search proteins (name, id, domain...)" />
      <button @click="search">Search</button>
    </div>

    <div v-if="loading">Loading…</div>
    <ul v-else>
      <li v-for="p in proteins" :key="p.protein_id">
        <router-link :to="`/proteins/${p.protein_id}`"
          >{{ p.protein_id }} — {{ p.name }}</router-link
        >
        <div class="meta">{{ p.description }}</div>
      </li>
    </ul>

    <Pagination
      v-if="total > limit"
      :total="total"
      :limit="limit"
      :page.sync="page"
      @change="search" />
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../services/api";
import Pagination from "../components/Pagination.vue";

const query = ref("");
const proteins = ref([]);
const loading = ref(false);
const limit = ref(20);
const page = ref(1);
const total = ref(0);

async function search() {
  loading.value = true;
  try {
    const resp = await api.searchProteins(query.value, limit.value, page.value);
    proteins.value = resp.items || resp || [];
    total.value = resp.total || proteins.value.length;
  } catch (e) {
    alert("Search error: " + e.message);
  } finally {
    loading.value = false;
  }
}

search();
</script>

<style>
.controls {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.meta {
  color: #666;
  font-size: 0.9rem;
}
</style>
