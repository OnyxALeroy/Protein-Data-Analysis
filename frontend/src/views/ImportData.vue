<template>
  <section>
    <h2>Import Data</h2>
    <div>
      <label
        >Upload protein JSON/CSV: <input type="file" @change="onFile"
      /></label>
      <button @click="upload" :disabled="!file">Upload</button>
    </div>
    <div>
      <label
        >Generate sample count:
        <input v-model.number="sampleCount" type="number"
      /></label>
      <button @click="generate">Generate</button>
    </div>
    <div v-if="message">{{ message }}</div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../services/api";
const file = ref(null);
const sampleCount = ref(100);
const message = ref("");

function onFile(e) {
  file.value = e.target.files[0];
}

async function upload() {
  const fd = new FormData();
  fd.append("file", file.value);
  try {
    const res = await api.importProteins(fd);
    message.value = "Uploaded";
  } catch (e) {
    message.value = "Upload failed: " + e.message;
  }
}

async function generate() {
  try {
    await api.generateSample(sampleCount.value);
    message.value = "Sample generated";
  } catch (e) {
    message.value = "Failed: " + e.message;
  }
}
</script>
