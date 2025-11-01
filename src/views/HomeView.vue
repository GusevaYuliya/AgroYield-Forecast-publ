<template>
  <div class="home-page">
    <div class="main-container">
      <!-- Левая часть -->
      <div class="left-section">
        <div class="content-wrapper">
          <h1 class="site-title">AgroYield Forecast</h1>
          <p class="site-description">
            Веб приложение для прогнозирования урожайности сельскохозяйственных культур
          </p>
          <div class="features-list">
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <span>Точные прогнозы урожайности</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🌱</span>
              <span>Анализ сельскохозяйственных культур</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">⏱️</span>
              <span>Экономия времени и ресурсов</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Правая часть -->
      <div class="right-section">
        <div class="content-wrapper">
          <h2 class="section-title">Начните работу</h2>
          <p class="section-description">
            Перейдите на дополнительную страницу для просмотра аналитики и отчетов
          </p>
          
          <router-link to="/second" class="cta-button">
            Перейти к аналитике →
          </router-link>

          <div class="quick-stats">
            <div class="stat-item">
              <div class="stat-value">Высокая</div>
              <div class="stat-label">точность прогнозов</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">Все</div>
              <div class="stat-label">основные сельскохозяйственные культуры</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Логика главной страницы
</script>

<style scoped>
/* Стили теперь в отдельном CSS файле */
</style>