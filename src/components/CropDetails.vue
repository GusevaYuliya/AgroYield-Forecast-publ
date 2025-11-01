<template>
  <div v-if="crop" class="crop-details">
    <div class="details-header">
      <span class="crop-icon-large">{{ crop.icon }}</span>
      <div class="crop-info">
        <h2 class="crop-title">{{ crop.name }}</h2>
        <p class="crop-description">{{ crop.description }}</p>
      </div>
    </div>
    
    <!-- Панель выбора региона -->
    <div class="region-selection">
      <h3>Выберите регион для просмотра статистики</h3>
      <div class="region-select-container">
        <select 
          v-model="selectedRegionId"
          @change="onRegionChange"
          class="region-select"
          size="1"
        >
          <option value="">Выберите регион</option>
          <optgroup 
            v-for="district in federalDistricts" 
            :key="district.name"
            :label="district.name"
          >
            <option 
              v-for="region in district.regions" 
              :key="region.id" 
              :value="region.id"
            >
              {{ region.name }}
            </option>
          </optgroup>
        </select>
        <div v-if="selectedRegion" class="selected-region-info">
          <p>Выбран регион: <strong>{{ selectedRegion.name }}</strong></p>
          <p class="district-info">Федеральный округ: {{ selectedRegion.federalDistrict }}</p>
        </div>
      </div>
    </div>
    
    <!-- Блок загрузки -->
    <div v-if="loading" class="loading-section">
      <div class="loading-spinner"></div>
      <p>Построение графика урожайности...</p>
    </div>
    
    <!-- Блок ошибки -->
    <div v-if="error" class="error-section">
      <p class="error-message">⚠️ {{ error }}</p>
      <button @click="fetchYieldChart" class="retry-button">Попробовать снова</button>
    </div>
    
    <div class="details-content">
      <!-- График урожайности -->
      <div v-if="yieldChartImage && selectedRegion" class="yield-chart-section">
        <h3>Динамика урожайности культуры {{ crop.name }} в регионе {{ selectedRegion.name }} на 2000-2026 год</h3>
        <div class="chart-container">
          <img 
            :src="'data:image/png;base64,' + yieldChartImage" 
            :alt="`График урожайности ${crop.name} в ${selectedRegion.name}`"
            class="yield-chart"
            @load="onChartLoad"
            @error="onChartError"
          />
          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-color historical"></span>
              <span>Исторические данные</span>
            </div>
            <div class="legend-item">
              <span class="legend-color forecast"></span>
              <span>Прогноз на 2025-2026 гг</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Блок расчёта урожая -->
      <div v-if="selectedRegion" class="field-calculation">
        <h3>Расчёт урожая на 2025 год</h3>
        
        <div class="input-section">
          <div class="input-group">
            <label for="field-area">Площадь вашего поля (гектары):</label>
            <div class="area-input-container">
              <input 
                type="number" 
                id="field-area"
                v-model.number="fieldArea"
                placeholder="Введите площадь"
                min="0"
                step="0.1"
                class="area-input"
              >
              <button 
                v-if="fieldArea > 0 && forecast2025 && canRefinePrediction"
                @click="toggleRefinement"
                class="refine-button"
                :class="{ active: showRefinedForm }"
              >
                {{ showRefinedForm ? 'Скрыть параметры' : 'Уточнить прогноз' }}
              </button>
            </div>
          </div>
          
          <!-- Базовый расчет -->
          <div class="calculation-result" v-if="fieldArea > 0 && forecast2025 && !refinedYield">
            <div class="result-card">
              <div class="result-value">{{ calculatedYield }} ц</div>
              <div class="result-label">
                Прогнозируемый урожай {{ crop.name }} на 2025 год
              </div>
              <div class="result-details">
                <span>{{ forecast2025.toFixed(1) }} ц/га × {{ fieldArea }} га</span>
              </div>
            </div>
          </div>

          <!-- Блок уточнённого прогноза -->
          <div v-if="canRefinePrediction && showRefinedForm && fieldArea > 0 && forecast2025" class="refined-prediction">
            <div class="refined-form">
              <h4>🔍 Уточнение прогноза с вашими параметрами</h4>
              
              <div class="form-grid">
                <!-- Тип почвы -->
                <div class="form-group">
                  <label for="soil-type">Тип почвы:</label>
                  <select 
                    id="soil-type"
                    v-model="refinedParams.soil_type"
                    class="form-select"
                  >
                    <option value="глинистая">Глинистая</option>
                    <option value="песчаная">Песчаная</option>
                    <option value="суглинистая">Суглинистая</option>
                    <option value="иловая">Иловая</option>
                    <option value="торфяная">Торфяная</option>
                    <option value="меловая">Меловая</option>
                  </select>
                </div>

                <!-- Количество осадков -->
                <div class="form-group">
                  <label for="rainfall">Осадки (мм):</label>
                  <input 
                    type="number" 
                    id="rainfall"
                    v-model.number="refinedParams.rainfall_mm"
                    min="0"
                    max="1000"
                    step="10"
                    class="form-input"
                    placeholder="300"
                  >
                  <div class="input-hint">Диапазон: 0-1000 мм</div>
                </div>

                <!-- Температура -->
                <div class="form-group">
                  <label for="temperature">Средняя температура (°C):</label>
                  <input 
                    type="number" 
                    id="temperature"
                    v-model.number="refinedParams.temperature_celsius"
                    min="-10"
                    max="40"
                    step="1"
                    class="form-input"
                    placeholder="20"
                  >
                  <div class="input-hint">Диапазон: -10°C до 40°C</div>
                </div>

                <!-- Удобрения -->
                <div class="form-group">
                  <label for="fertilizer">Использование удобрений:</label>
                  <select 
                    id="fertilizer"
                    v-model="refinedParams.fertilizer_used"
                    class="form-select"
                  >
                    <option :value="true">Да</option>
                    <option :value="false">Нет</option>
                  </select>
                </div>

                <!-- Орошение -->
                <div class="form-group">
                  <label for="irrigation">Использование орошения:</label>
                  <select 
                    id="irrigation"
                    v-model="refinedParams.irrigation_used"
                    class="form-select"
                  >
                    <option :value="true">Да</option>
                    <option :value="false">Нет</option>
                  </select>
                </div>

                <!-- Погодные условия -->
                <div class="form-group">
                  <label for="weather">Погодные условия:</label>
                  <select 
                    id="weather"
                    v-model="refinedParams.weather_condition"
                    class="form-select"
                  >
                    <option value="солнечно">Солнечно</option>
                    <option value="дождливо">Дождливо</option>
                    <option value="облачно">Облачно</option>
                  </select>
                </div>

                <!-- Дни до урожая -->
                <div class="form-group">
                  <label for="days">Дней до урожая:</label>
                  <input 
                    type="number" 
                    id="days"
                    v-model.number="refinedParams.days_to_harvest"
                    min="60"
                    max="180"
                    step="1"
                    class="form-input"
                    placeholder="120"
                  >
                  <div class="input-hint">Диапазон: 60-180 дней</div>
                </div>
              </div>

              <div class="refined-actions">
                <button 
                  @click="fetchRefinedPrediction" 
                  :disabled="refinedLoading"
                  class="calculate-refined-btn"
                >
                  <span v-if="refinedLoading">⏳ Расчет...</span>
                  <span v-else>🎯 Рассчитать уточнённый прогноз</span>
                </button>

                <button 
                  @click="resetRefinement"
                  class="reset-refined-btn"
                >
                  Сбросить параметры
                </button>
              </div>

              <!-- Результат уточнённого прогноза -->
              <div v-if="refinedYield && !refinedLoading" class="refined-result">
                <div class="result-comparison">
                  <div class="comparison-item original">
                    <div class="comparison-label">Базовый прогноз</div>
                    <div class="comparison-value">{{ forecast2025.toFixed(1) }} ц/га</div>
                    <div class="comparison-note">(на основе исторических данных)</div>
                  </div>
                  <div class="comparison-arrow">→</div>
                  <div class="comparison-item refined">
                    <div class="comparison-label">Уточнённый прогноз</div>
                    <div class="comparison-value">{{ refinedYield.toFixed(1) }} ц/га</div>
                    <div class="comparison-note">(с учётом ваших параметров)</div>
                  </div>
                </div>
                
                <div class="difference-indicator" :class="getDifferenceClass()">
                  <span v-if="yieldDifference > 0">📈 +{{ yieldDifference.toFixed(1) }} ц/га</span>
                  <span v-else-if="yieldDifference < 0">📉 {{ yieldDifference.toFixed(1) }} ц/га</span>
                  <span v-else>➡️ Без изменений</span>
                  <span class="difference-text">{{ getDifferenceText() }}</span>
                </div>
                
                <div class="refined-calculation">
                  <div class="refined-total">
                    <div class="total-value">{{ Math.round(refinedYield * fieldArea) }} ц</div>
                    <div class="total-label">
                      Уточнённый урожай {{ crop.name }} на 2025 год
                    </div>
                    <div class="total-details">
                      <span>{{ refinedYield.toFixed(1) }} ц/га × {{ fieldArea }} га</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="refinedError" class="refined-error">
                <p>⚠️ {{ refinedError }}</p>
                <button @click="fetchRefinedPrediction" class="retry-button">Попробовать снова</button>
              </div>
            </div>
          </div>
          
          <div class="no-forecast-message" v-else-if="fieldArea > 0 && !forecast2025 && !loading">
            <p>⚠️ Прогноз на 2025 год недоступен для расчёта</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  
  <div v-else class="no-selection">
    <div class="placeholder-icon">🌱</div>
    <h3>Выберите культуру</h3>
    <p>Нажмите на одну из культур выше, чтобы увидеть детальную информацию и прогноз урожайности</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useCropsStore } from '@/stores/crops'
import type { Crop } from '@/types/crops'
import type { Region } from '@/stores/crops'

interface Props {
  crop: Crop | null
}

const props = defineProps<Props>()
const cropsStore = useCropsStore()
const selectedRegionId = ref('')
const yieldChartImage = ref<string | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const forecast2025 = ref<number | null>(null)
const fieldArea = ref<number>(1000)

// Переменные для уточненного прогноза
const showRefinedForm = ref(false)
const refinedLoading = ref(false)
const refinedError = ref<string | null>(null)
const refinedYield = ref<number | null>(null)

const cropsWithRefinedPrediction = ['Пшеница озимая', 'Кукуруза', 'Рис', 'Соя']

// Проверка, доступен ли уточненный прогноз для текущей культуры
const canRefinePrediction = computed(() => {
  return props.crop ? cropsWithRefinedPrediction.includes(props.crop.name) : false
})

const refinedParams = ref({
  soil_type: 'глинистая',
  rainfall_mm: 300,
  temperature_celsius: 20,
  fertilizer_used: true,
  irrigation_used: true,
  weather_condition: 'солнечно',
  days_to_harvest: 120
})

const calculatedYield = computed(() => {
  if (!forecast2025.value || fieldArea.value <= 0) return 0
  return Math.round(forecast2025.value * fieldArea.value)
})

const selectedRegion = computed(() => cropsStore.selectedRegion)

// Разница между базовым и уточненным прогнозом
const yieldDifference = computed(() => {
  if (!refinedYield.value || !forecast2025.value) return 0
  return refinedYield.value - forecast2025.value
})

const getDifferenceClass = () => {
  if (yieldDifference.value > 0) return 'positive'
  if (yieldDifference.value < 0) return 'negative'
  return 'neutral'
}

const getDifferenceText = () => {
  if (yieldDifference.value > 0) return 'Улучшение прогноза'
  if (yieldDifference.value < 0) return 'Снижение прогноза'
  return 'Прогноз без изменений'
}

// Данные для отладки - что отправляется на бэкенд
const debugRequestData = computed(() => {
  return {
    crop_name: props.crop?.name,
    region: selectedRegion.value?.name,
    api_url: 'http://localhost:8000/api/yield-chart',
    request_body: props.crop && selectedRegion.value ? {
      crop_name: props.crop.name,
      region: selectedRegion.value.name
    } : null
  }
})

// Группируем регионы по федеральным округам
const federalDistricts = computed(() => {
  const districtsMap = new Map()
  
  cropsStore.regions.forEach(region => {
    if (!districtsMap.has(region.federalDistrict)) {
      districtsMap.set(region.federalDistrict, {
        name: region.federalDistrict,
        regions: []
      })
    }
    districtsMap.get(region.federalDistrict).regions.push(region)
  })
  
  return Array.from(districtsMap.values())
})

const onRegionChange = (event: Event) => {
  console.log('🔄 Region change event:', event)
  const target = event.target as HTMLSelectElement
  const regionId = target.value
  console.log('📍 Selected region ID:', regionId)
  
  if (regionId) {
    const region = cropsStore.regions.find(r => r.id === regionId)
    console.log('🔍 Found region:', region)
    if (region) {
      cropsStore.selectRegion(region)
      console.log('✅ Region selected:', region.name)
    }
  } else {
    console.log('❌ No region selected')
    cropsStore.selectRegion(null as any)
    yieldChartImage.value = null
    forecast2025.value = null
  }
}

// Обработчики для изображения графика
const onChartLoad = () => {
  console.log('✅ Chart image loaded successfully')
}

const onChartError = (event: Event) => {
  console.error('❌ Chart image failed to load:', event)
  error.value = 'Ошибка загрузки изображения графика'
}

// Функции для уточненного прогноза
const toggleRefinement = () => {
  showRefinedForm.value = !showRefinedForm.value
  if (!showRefinedForm.value) {
    // При скрытии формы сбрасываем результаты уточненного прогноза
    refinedYield.value = null
    refinedError.value = null
  }
}

const resetRefinement = () => {
  refinedParams.value = {
    soil_type: 'глинистая',
    rainfall_mm: 300,
    temperature_celsius: 20,
    fertilizer_used: true,
    irrigation_used: true,
    weather_condition: 'солнечно',
    days_to_harvest: 120
  }
  refinedYield.value = null
  refinedError.value = null
}

const fetchRefinedPrediction = async () => {
  if (!props.crop || !selectedRegion.value) {
    refinedError.value = 'Не выбрана культура или регион'
    return
  }

  refinedLoading.value = true
  refinedError.value = null

  try {
    const apiUrl = 'http://localhost:8000/api/refined-yield'
    
    const requestBody = {
      crop_name: props.crop.name,
      region: selectedRegion.value.name,
      field_area: fieldArea.value,
      base_yield: forecast2025.value,
      ...refinedParams.value
    }
    
    console.log('📤 Sending refined prediction request:', requestBody)

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Refined prediction API error:', errorText)
      let errorDetail = 'Ошибка при расчёте уточнённого прогноза'
      
      try {
        const errorData = JSON.parse(errorText)
        errorDetail = errorData.detail || errorText
      } catch {
        errorDetail = errorText || `HTTP error! status: ${response.status}`
      }
      
      throw new Error(errorDetail)
    }

    const data = await response.json()
    console.log('✅ Refined prediction response:', data)

    refinedYield.value = data.refined_yield

  } catch (err) {
    console.error('💥 Error in fetchRefinedPrediction:', err)
    refinedError.value = err instanceof Error ? err.message : 'Не удалось рассчитать уточнённый прогноз'
  } finally {
    refinedLoading.value = false
  }
}

// Функция для получения графика урожайности
const fetchYieldChart = async () => {
  console.log('🚀 Starting fetchYieldChart...')
  
  if (!props.crop || !selectedRegion.value) {
    console.log('❌ Missing required data - crop or region')
    console.log('🌱 Crop:', props.crop?.name)
    console.log('📍 Region:', selectedRegion.value?.name)
    yieldChartImage.value = null
    forecast2025.value = null
    return
  }

  loading.value = true
  error.value = null
  yieldChartImage.value = null
  forecast2025.value = null

  try {
    console.log('🌐 Making API request to backend...')
    const apiUrl = 'http://localhost:8000/api/yield-chart'
    
    const requestBody = {
      crop_name: props.crop.name,
      region: selectedRegion.value.name
    }
    
    console.log('📤 Sending request with data:', requestBody)
    console.log('📍 Region name being sent:', JSON.stringify(requestBody.region))

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    })

    console.log('📨 Response status:', response.status)
    console.log('📨 Response ok:', response.ok)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ API error response:', errorText)
      let errorDetail = 'Ошибка при загрузке графика'
      
      try {
        const errorData = JSON.parse(errorText)
        errorDetail = errorData.detail || errorText
      } catch {
        errorDetail = errorText || `HTTP error! status: ${response.status}`
      }
      
      throw new Error(errorDetail)
    }

    const data = await response.json()
    console.log('✅ API success response received')
    console.log('📊 Response data:', data)

    if (!data.chart_image) {
      throw new Error('Пустой ответ от сервера - отсутствует изображение графика')
    }

    yieldChartImage.value = data.chart_image
    forecast2025.value = data.forecast_2025 || null

    console.log('🎉 Chart successfully loaded')
    console.log('📊 Forecast 2025:', forecast2025.value)

  } catch (err) {
    console.error('💥 Error in fetchYieldChart:', err)
    error.value = err instanceof Error ? err.message : 'Не удалось загрузить график урожайности'
  } finally {
    loading.value = false
  }
}

// Автоматически загружаем график при изменении культуры или региона
watch([() => props.crop, selectedRegion], () => {
  console.log('👀 Watcher triggered - crop or region changed')
  console.log('🌱 Crop:', props.crop?.name)
  console.log('📍 Region:', selectedRegion.value?.name)
  
  if (props.crop && selectedRegion.value) {
    console.log('✅ Conditions met, fetching chart...')
    fetchYieldChart()
  } else {
    console.log('❌ Conditions not met, clearing chart')
    yieldChartImage.value = null
    forecast2025.value = null
  }
}, { immediate: true })

// Логирование при монтировании
console.log('🔧 CropDetails component mounted')
console.log('📊 Available regions:', cropsStore.regions.map(r => r.name))
</script>

<style scoped>
.area-input-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.refine-button {
  background: #ff9800;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.refine-button:hover {
  background: #f57c00;
  transform: translateY(-1px);
}

.refine-button.active {
  background: #f57c00;
}

.refined-prediction {
  margin-top: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

.refined-form h4 {
  margin-bottom: 20px;
  color: #333;
  font-size: 18px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 6px;
  color: #555;
}

.form-input,
.form-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.input-hint {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

.refined-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.calculate-refined-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.calculate-refined-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.reset-refined-btn {
  background: #757575;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.result-comparison {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 30px;
  margin: 20px 0;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.comparison-item {
  text-align: center;
  padding: 15px;
  border-radius: 6px;
}

.comparison-item.original {
  background: #e3f2fd;
  border: 1px solid #2196f3;
}

.comparison-item.refined {
  background: #e8f5e8;
  border: 1px solid #4caf50;
}

.comparison-label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.comparison-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.comparison-item.original .comparison-value {
  color: #2196f3;
}

.comparison-item.refined .comparison-value {
  color: #4caf50;
}

.comparison-note {
  font-size: 12px;
  color: #666;
}

.comparison-arrow {
  font-size: 24px;
  color: #666;
}

.difference-indicator {
  text-align: center;
  padding: 10px;
  border-radius: 6px;
  margin: 15px 0;
  font-weight: 600;
}

.difference-indicator.positive {
  background: #e8f5e8;
  color: #2e7d32;
}

.difference-indicator.negative {
  background: #ffebee;
  color: #c62828;
}

.difference-indicator.neutral {
  background: #f5f5f5;
  color: #666;
}

.difference-text {
  display: block;
  font-size: 14px;
  font-weight: normal;
  margin-top: 4px;
}

.refined-total {
  background: linear-gradient(135deg, #4caf50, #45a049);
  color: white;
  padding: 25px;
  border-radius: 10px;
  text-align: center;
  margin-top: 20px;
}

.total-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.total-label {
  font-size: 16px;
  margin-bottom: 8px;
  opacity: 0.9;
}

.total-details {
  font-size: 14px;
  opacity: 0.8;
}

.refined-error {
  background: #ffebee;
  color: #c62828;
  padding: 15px;
  border-radius: 6px;
  margin-top: 15px;
  text-align: center;
}

/* Остальные существующие стили остаются без изменений */
</style>