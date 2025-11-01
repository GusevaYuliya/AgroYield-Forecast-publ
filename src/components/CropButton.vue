<template>
  <button 
    :class="['crop-button', { active: isActive }]"
    :style="{ '--crop-color': crop.color }"
    @click="handleClick"
  >
    <span class="crop-icon">{{ crop.icon }}</span>
    <span class="crop-name">{{ crop.name }}</span>
  </button>
</template>

<script setup lang="ts">
import type { Crop } from '@/types/crops'

interface Props {
  crop: Crop
  isActive: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [crop: Crop]
}>()

const handleClick = () => {
  emit('select', props.crop)
}
</script>

<style scoped>
/* Стили перенесены в src/styles/components/crop-button.css */
</style>