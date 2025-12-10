<template>
  <section v-if="protein">
    <h2>{{ protein.protein_id }} — {{ protein.name }}</h2>
    <p>{{ protein.description }}</p>
    <dl>
      <dt>Length</dt>
      <dd>{{ protein.length }}</dd>
      <dt>Taxonomy</dt>
      <dd>{{ protein.taxonomy_name }} ({{ protein.taxonomy_id }})</dd>
      <dt>EC</dt>
      <dd>{{ protein.ec_numbers?.join(", ") }}</dd>
      <dt>GO terms</dt>
      <dd>{{ protein.go_terms?.join(", ") }}</dd>
    </dl>

    <h3>Domains</h3>
    <ul>
      <li v-for="d in domains" :key="d.domain_id">
        {{ d.domain_id }} — {{ d.domain_name }}
      </li>
    </ul>

    <button @click="getSimilar">Find similar proteins</button>
    <ul v-if="similar.length">
      <li v-for="s in similar" :key="s.protein_id">
        <router-link :to="`/proteins/${s.protein_id}`"
          >{{ s.protein_id }} — {{ s.name }}</router-link
        >
        <small>sim: {{ s.similarity }}</small>
      </li>
    </ul>
  </section>
  <div v-else>Loading…</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { api } from "../services/api";
import { useRoute } from "vue-router";

const route = useRoute();
const protein = ref(null);
const domains = ref([]);
const similar = ref([]);

async function load() {
  const id = route.params.proteinId;
  protein.value = await api.getProtein(id);
  domains.value = await api.getProteinDomains(id);
}

async function getSimilar() {
  similar.value = await api.getProteinSimilar(route.params.proteinId);
}

onMounted(load);
</script>
