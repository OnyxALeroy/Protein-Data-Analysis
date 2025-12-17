<template>
  <section>
    <h2>Import Data</h2>
    <div>
      <label
        >Upload protein JSON/CSV: <input type="file" @change="onFile"
      /></label>
      <button @click="upload" :disabled="!file || uploading">Upload</button>
    </div>
    <div>
      <label
        >Generate sample count:
        <input v-model.number="sampleCount" type="number"
      /></label>
      <button @click="generate" :disabled="generating">Generate</button>
    </div>
    <div v-if="uploading">Uploading…</div>
    <div v-else-if="generating">Generating…</div>
    <div v-if="message">{{ message }}</div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../services/api";
const file = ref(null);
const sampleCount = ref(100);
const message = ref("");
const uploading = ref(false);
const generating = ref(false);

function onFile(e) {
  file.value = e.target.files[0];
}

async function upload() {
  uploading.value = true;
  const fd = new FormData();
  fd.append("file", file.value);
  try {
    const res = await api.importProteins(fd);
    message.value = "Uploaded";
  } catch (e) {
    message.value = "Upload failed: " + e.message;
  } finally {
    uploading.value = false;
  }
}

async function generate() {
  generating.value = true;
  try {
    await api.generateSample(sampleCount.value);
    message.value = "Sample generated";
  } catch (e) {
    message.value = "Failed: " + e.message;
  } finally {
    generating.value = false;
  }
}
</script>
