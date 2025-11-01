export interface Crop {
  id: number
  name: string
  icon: string
  color: string
  description: string
}

export interface CropsState {
  selectedCrop: Crop | null
  crops: Crop[]
}