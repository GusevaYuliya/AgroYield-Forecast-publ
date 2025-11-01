<template>
  <div class="second-page">
    <div class="page-container">
      <!-- Заголовок страницы -->
      <header class="page-header">
        <h1 class="page-title">Прогноз урожайности</h1>
        <p class="page-description">
          Выберите сельскохозяйственную культуру для просмотра детальной аналитики и прогноза урожайности
        </p>
      </header>

      <!-- Панель выбора культур -->
      <section class="crops-panel">
        <h2 class="panel-title">Доступные культуры</h2>
        <div class="crops-grid">
          <CropButton
            v-for="crop in cropsStore.crops"
            :key="crop.id"
            :crop="crop"
            :is-active="cropsStore.selectedCrop?.id === crop.id"
            @select="cropsStore.selectCrop"
          />
        </div>
      </section>

      <!-- Детальная информация о выбранной культуре -->
      <CropDetails :crop="cropsStore.selectedCrop" />

      <!-- Кнопка возврата -->
      <footer class="page-footer">
        <router-link to="/" class="back-button">
          ← Вернуться на главную
        </router-link>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useCropsStore } from '@/stores/crops'
import CropButton from '@/components/CropButton.vue'
import CropDetails from '@/components/CropDetails.vue'

const cropsStore = useCropsStore()
</script>

<style scoped>
/* Стили перенесены в src/styles/components/second-page.css */
</style>