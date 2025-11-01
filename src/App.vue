<template>
  <div id="app">
    <!-- Навигационное меню показываем только НА второй странице -->
    <nav class="navigation" v-if="$route.name === 'second'">
      <router-link to="/" class="nav-link">
        ← На главную
      </router-link>
    </nav>

    <!-- Область для отображения страниц -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Футер показываем только НА второй странице -->
    <footer class="app-footer" v-if="$route.name === 'second'">
      <p>AgroYield Forecast - Система прогнозирования урожайности</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const $route = useRoute()
</script>

<style scoped>
/* Стили теперь в отдельном CSS файле */
</style>
