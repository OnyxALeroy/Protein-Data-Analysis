<template>
  <div id="app">
    <Navbar />
    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import Navbar from "./components/Navbar.vue";
</script>

<style>
.container {
  max-width: 1100px;
  margin: 1rem auto;
  padding: 1rem;
}
</style>

