<template>
  <nav class="nav">
    <router-link to="/">Home</router-link>
    <router-link to="/proteins">Proteins</router-link>
    <router-link to="/graph/build">Graph</router-link>
    <router-link to="/statistics">Statistics</router-link>
    <router-link to="/annotation/propagate">Annotation</router-link>
    <router-link to="/import">Import</router-link>
  </nav>
</template>

<script setup></script>

<style>
.nav {
  display: flex;
  gap: 1rem;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}
</style>
