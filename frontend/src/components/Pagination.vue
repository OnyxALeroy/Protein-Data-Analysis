<template>
  <div class="pagination">
    <button :disabled="page <= 1" @click="setPage(page - 1)">Prev</button>
    <span>Page {{ page }} / {{ pages }}</span>
    <button :disabled="page >= pages" @click="setPage(page + 1)">Next</button>
  </div>
</template>

<script setup>
import { computed, toRefs } from "vue";
const props = defineProps({ total: Number, limit: Number, page: Number });
const emit = defineEmits(["change", "update:page"]);
const pages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)));
function setPage(n) {
  emit("update:page", n);
  emit("change", n);
}
</script>

<style>
.pagination {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-top: 1rem;
}
</style>
