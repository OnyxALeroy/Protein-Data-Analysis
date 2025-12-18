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
      <li v-for="d in domains" :key="d">
        {{ d }}
      </li>
    </ul>

    <button @click="getSimilar" :disabled="loading">Find similar proteins</button>
    <div v-if="loading">Loading similar proteins…</div>
    <ul v-if="similar.length">
      <li v-for="s in similar" :key="s.protein_id">
        <router-link :to="`/proteins/${s.protein_id}`"
          >{{ s.protein_id }} — {{ s.name }}</router-link
        >
        <small>sim: {{ s.similarity }}</small>
      </li>
    </ul>

    <h3>Neighbour Graph</h3>
    <button @click="getNeighbors" :disabled="neighborsLoading">Load neighbours</button>
    <div v-if="neighborsLoading">Loading neighbours…</div>
    <div id="graph-container" v-if="neighbors.length"></div>
  </section>
  <div v-else>Loading…</div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { api } from "../services/api";
import { useRoute } from "vue-router";
import * as d3 from "d3";

const route = useRoute();
const protein = ref(null);
const domains = ref([]);
const similar = ref([]);
const loading = ref(false);
const neighbors = ref([]);
const neighborsLoading = ref(false);

async function load() {
  const id = route.params.proteinId;
  protein.value = await api.getProtein(id);
  domains.value = await api.getProteinDomains(id);
}

async function getSimilar() {
  loading.value = true;
  try {
    similar.value = await api.getProteinSimilar(route.params.proteinId);
  } catch (e) {
    alert("Failed to load similar proteins: " + e.message);
  } finally {
    loading.value = false;
  }
}

async function getNeighbors() {
  neighborsLoading.value = true;
  try {
    const graphData = await api.graphNeighbors(route.params.proteinId);
    neighbors.value = graphData.nodes.filter(n => n.protein_id !== protein.value.protein_id);
    await nextTick();
    renderGraph();
  } catch (e) {
    alert("Failed to load neighbours: " + e.message);
  } finally {
    neighborsLoading.value = false;
  }
}

function renderGraph() {
  const container = d3.select("#graph-container");
  container.selectAll("*").remove();

  const width = 600;
  const height = 400;
  
  const svg = container.append("svg")
    .attr("width", width)
    .attr("height", height);

  const nodes = [
    { id: protein.value.protein_id, type: "center" },
    ...neighbors.value.map(n => ({ id: n.protein_id, type: "neighbor" }))
  ];

  const links = neighbors.value.map(n => ({
    source: protein.value.protein_id,
    target: n.protein_id
  }));

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2));

  const link = svg.append("g")
    .selectAll("line")
    .data(links)
    .enter().append("line")
    .attr("stroke", "#ddd")
    .attr("stroke-width", 2);

  const node = svg.append("g")
    .selectAll("g")
    .data(nodes)
    .enter().append("g")
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended));

  node.append("circle")
    .attr("r", d => d.type === "center" ? 20 : 15)
    .attr("fill", d => d.type === "center" ? "#ff6b6b" : "#4ecdc4");

  node.append("text")
    .text(d => d.id)
    .attr("text-anchor", "middle")
    .attr("dy", ".35em")
    .attr("fill", "white")
    .attr("font-size", d => d.type === "center" ? "12px" : "10px");

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });

  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
}

onMounted(load);
</script>
