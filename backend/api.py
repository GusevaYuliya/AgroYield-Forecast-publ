from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error
import os
import traceback
from pydantic import BaseModel
import logging
from catboost import CatBoostRegressor, Pool

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'catboost_model.cbm')

try:
    catboost_model = CatBoostRegressor()
    catboost_model.load_model(model_path)
    logger.info("✅ CatBoost model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load CatBoost model: {e}")
    catboost_model = None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class YieldRequest(BaseModel):
    crop_name: str
    region: str

class RefinedPredictionRequest(BaseModel):
    crop_name: str
    region: str
    field_area: float
    base_yield: float
    soil_type: str
    rainfall_mm: float
    temperature_celsius: float
    fertilizer_used: bool
    irrigation_used: bool
    weather_condition: str
    days_to_harvest: int

REGION_MAPPING = {
    'Север': 'North',
    'Восток': 'East', 
    'Юг': 'South',
    'Запад': 'West'
}

SOIL_TYPE_MAPPING = {
    'глинистая': 'Clay',
    'песчаная': 'Sandy',
    'суглинистая': 'Loam',
    'иловая': 'Silt',
    'торфяная': 'Peaty',
    'меловая': 'Chalky'
}

CROP_MAPPING = {
    'Пшеница озимая': 'Wheat',
    'Рис': 'Rice',
    'Кукуруза': 'Maize',
    'Ячмень': 'Barley',
    'Соя': 'Soybean',
    'Хлопок': 'Cotton'
}

WEATHER_MAPPING = {
    'солнечно': 'Sunny',
    'дождливо': 'Rainy',
    'облачно': 'Cloudy'
}

def generate_yield_forecast(culture: str, region: str) -> str:
    """
    Функция для построения графика урожайности с прогнозом
    """
    logger.info(f"🚀 Starting generate_yield_forecast for crop: '{culture}', region: '{region}'")
    
    try:
        # Путь к CSV файлам относительно расположения api.py
        csv_path = os.path.join(current_dir, f'data/{culture}.csv')
        logger.info(f"📁 Looking for CSV file: {csv_path}")
        
        if not os.path.exists(csv_path):
            error_msg = f"CSV файл для культуры '{culture}' не найден по пути: {csv_path}"
            logger.error(f"❌ {error_msg}")
            logger.info(f"📂 Current working directory: {os.getcwd()}")
            logger.info(f"📂 Files in data directory: {os.listdir('data') if os.path.exists('data') else 'data directory not found'}")
            raise FileNotFoundError(error_msg)
        
        logger.info(f"✅ CSV file found, reading data...")
        df = pd.read_csv(csv_path)
        logger.info(f"📊 CSV loaded successfully. Columns: {df.columns.tolist()}")
        logger.info(f"📊 CSV shape: {df.shape}")
        
        # Проверяем наличие колонки 'Регион'
        if 'Регион' not in df.columns:
            error_msg = f"Колонка 'Регион' не найдена в CSV файле. Доступные колонки: {df.columns.tolist()}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info(f"🔍 Looking for region: '{region}'")
        logger.info(f"📋 Available regions in CSV: {df['Регион'].tolist()}")
        
        # Проверяем точное соответствие региона
        exact_match = df[df['Регион'] == region]
        logger.info(f"📍 Exact match found: {len(exact_match)} rows")
        
        if len(exact_match) == 0:
            # Проверяем частичные совпадения для отладки
            partial_matches = df[df['Регион'].str.contains(region, case=False, na=False)]
            logger.info(f"🔎 Partial matches for '{region}': {partial_matches['Регион'].tolist() if len(partial_matches) > 0 else 'No partial matches'}")
            
            error_msg = f"Регион '{region}' не найден в данных для культуры '{culture}'. Доступные регионы: {df['Регион'].tolist()}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        region_data = exact_match
        logger.info(f"📈 Found {len(region_data)} rows for region '{region}'")
        
        data_values = list(region_data.values)[0][1:]
        logger.info(f"📐 Data values length: {len(data_values)}")
        logger.info(f"📐 First 5 data values: {data_values[:5]}")
        
        data = np.array(data_values, dtype=float)
        logger.info(f"🔢 Converted to numpy array, shape: {data.shape}")
        
        # Поиск лучших параметров ARIMA
        logger.info("🔍 Starting ARIMA parameter search...")
        best_mae = np.inf
        best_order = None

        for p in range(0, 4):
            for d in range(0, 2):
                for q in range(0, 4):
                    try:
                        model = ARIMA(data, order=(p, d, q))
                        model_fit = model.fit()
                        preds = model_fit.predict()
                        mae = mean_absolute_error(data, preds)
                        if mae < best_mae:
                            best_mae = mae
                            best_order = (p, d, q)
                            logger.info(f"✅ Found better parameters: {best_order} with MAE: {best_mae:.4f}")
                    except Exception as e:
                        logger.debug(f"❌ ARIMA failed for order {(p, d, q)}: {str(e)}")
                        continue

        if best_order is None:
            error_msg = "Не удалось найти подходящие параметры ARIMA"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
            
        logger.info(f"🎯 Best ARIMA parameters: {best_order} with MAE: {best_mae:.4f}")

        # Финальная модель
        logger.info("🏗️ Building final ARIMA model...")
        final_model = ARIMA(data, order=best_order)
        final_model_fit = final_model.fit()

        # Подготовка данных
        row_data = df.loc[df['Регион'] == region].iloc[0]
        years = list(row_data.index[1:])
        yields = list(row_data.values[1:])
        
        logger.info(f"📅 Years: {years}")
        logger.info(f"📊 Yields (first 5): {yields[:5]}")

        # Прогноз
        logger.info("🔮 Making forecasts...")
        forecast_2025 = final_model_fit.forecast(steps=1)[0]
        forecast_2026 = final_model_fit.forecast(steps=2)[1]

        years.extend(['2025', '2026'])
        yields.extend([forecast_2025, forecast_2026])
        
        logger.info(f"🎯 Forecast 2025: {forecast_2025:.2f}")
        logger.info(f"🎯 Forecast 2026: {forecast_2026:.2f}")

        # Построение графика
        logger.info("📈 Creating matplotlib figure...")
        plt.figure(figsize=(20, 10))
        plt.style.use('seaborn-v0_8-whitegrid')

        colors = []
        for year in years:
            if year in ['2025', '2026']:
                colors.append('#FF6B35')
            else:
                colors.append('#2E8B57')

        bars = plt.bar(years, yields, color=colors, edgecolor='white', 
                      linewidth=3, alpha=0.95, zorder=3, width=0.7)

        # Добавление подписей для прогнозных значений
        for bar, value, year in zip(bars, yields, years):
            if not pd.isna(value) and year in ['2025', '2026']:
                height = bar.get_height()
                label = f'{value:.1f}'
                plt.text(bar.get_x() + bar.get_width()/2., height + max(yields)*0.02,
                       label, ha='center', va='bottom', fontweight='bold',
                       fontsize=16, color='#FFFFFF',
                       bbox=dict(boxstyle="round,pad=0.4", facecolor='#FF6B35', 
                               alpha=0.9, edgecolor='#FF8C42'))


        plt.xlabel('Годы', fontsize=20, fontweight='bold', labelpad=20, color='#2C3E50')
        plt.ylabel('Урожайность, ц/га', fontsize=20, fontweight='bold', labelpad=20, color='#2C3E50')
        
        plt.xticks(rotation=45, fontsize=16)
        plt.yticks(fontsize=16)
        
        plt.grid(axis='y', alpha=0.2, zorder=0, linestyle='--')
        plt.gca().set_facecolor('#F8F9FA')
        for spine in plt.gca().spines.values():
            spine.set_visible(False)
        
        plt.ylim(0, max(yields) * 1.15)

        # Легенда
        legend_elements = [
            Patch(facecolor='#2E8B57', alpha=0.95, label='Исторические данные', edgecolor='white', linewidth=2),
            Patch(facecolor='#FF6B35', alpha=1.0, label='Прогноз', edgecolor='#FFB38A', linewidth=2.5)
        ]

        plt.legend(handles=legend_elements, loc='upper left', 
                  frameon=True, fancybox=True, shadow=True, 
                  fontsize=18, facecolor='#FFFFFF')

        plt.tight_layout()
        
        # Конвертация в base64
        logger.info("🔄 Converting plot to base64...")
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='#F8F9FA')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        logger.info(f"✅ Successfully generated chart, base64 length: {len(img_base64)}")
        return {
            'chart_image': img_base64,
            'forecast_2025': float(forecast_2025),
            'forecast_2026': float(forecast_2026)
        }
        
    except Exception as e:
        logger.error(f"💥 Error in generate_yield_forecast: {str(e)}")
        logger.error(f"📝 Stack trace: {traceback.format_exc()}")
        plt.close()
        raise

@app.post("/api/yield-chart")
async def get_yield_chart(request: YieldRequest):
    logger.info(f"📥 Received request for crop: '{request.crop_name}', region: '{request.region}'")
    logger.info(f"🔍 Request details - crop_name type: {type(request.crop_name)}, region type: {type(request.region)}")
    logger.info(f"🔍 Request details - crop_name repr: {repr(request.crop_name)}, region repr: {repr(request.region)}")
    
    try:
        result = generate_yield_forecast(request.crop_name, request.region)
        
        # Извлекаем chart_image из словаря
        chart_image = result['chart_image']
        
        logger.info(f"📊 Generated chart - Length: {len(chart_image)}")
        response_data = {
            "chart_image": chart_image,  # Теперь это строка base64
            "crop_name": request.crop_name,
            "region": request.region,
            "forecast_2025": result.get('forecast_2025'),
            "forecast_2026": result.get('forecast_2026'),
            "status": "success"
        }
        
        logger.info(f"📤 Sending response, image length: {len(chart_image)}")
        return response_data
        
    except FileNotFoundError as e:
        logger.error(f"❌ FileNotFoundError: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Internal server error: {str(e)}")
        logger.error(f"📝 Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    logger.info("🔍 Health check requested")
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/api/debug/regions/{crop_name}")
async def debug_regions(crop_name: str):
    """Endpoint для отладки - показывает регионы для конкретной культуры"""
    logger.info(f"🔍 Debug regions requested for crop: {crop_name}")
    try:
        csv_path = f'data/{crop_name}.csv'
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            regions = df['Регион'].tolist() if 'Регион' in df.columns else []
            return {
                "crop_name": crop_name,
                "csv_file": csv_path,
                "regions": regions,
                "regions_count": len(regions)
            }
        else:
            return {"error": f"CSV file for crop '{crop_name}' not found"}
    except Exception as e:
        return {"error": str(e)}
    
def transform_russian_to_english(params: dict) -> dict:
    """
    Преобразует русские названия в английские, которые ожидает CatBoost модель
    """
    transformed = params.copy()
    
    # Преобразуем регион
    if params['region'] in REGION_MAPPING:
        transformed['region'] = REGION_MAPPING[params['region']]
    
    # Преобразуем тип почвы
    if params['soil_type'] in SOIL_TYPE_MAPPING:
        transformed['soil_type'] = SOIL_TYPE_MAPPING[params['soil_type']]
    
    # Преобразуем культуру
    if params['crop'] in CROP_MAPPING:
        transformed['crop'] = CROP_MAPPING[params['crop']]
    
    # Преобразуем погодные условия
    if params['weather'] in WEATHER_MAPPING:
        transformed['weather'] = WEATHER_MAPPING[params['weather']]
    
    # Преобразуем boolean в Yes/No
    transformed['fertilizer'] = 'Yes' if params['fertilizer'] else 'No'
    transformed['irrigation'] = 'Yes' if params['irrigation'] else 'No'
    
    return transformed

def catboost_predict(model, region, soil_type, crop, rainfall, temperature, fertilizer, irrigation, weather, days):
    """
    Функция для предсказания с использованием CatBoost модели
    """
    logger.info(f"🤖 Making CatBoost prediction with params:")
    logger.info(f"  - Region: {region}")
    logger.info(f"  - Soil Type: {soil_type}")
    logger.info(f"  - Crop: {crop}")
    logger.info(f"  - Rainfall: {rainfall} mm")
    logger.info(f"  - Temperature: {temperature} °C")
    logger.info(f"  - Fertilizer: {fertilizer}")
    logger.info(f"  - Irrigation: {irrigation}")
    logger.info(f"  - Weather: {weather}")
    logger.info(f"  - Days to harvest: {days}")
    
    input_data = pd.DataFrame({
        'Region': [region],
        'Soil_Type': [soil_type],
        'Crop': [crop],
        'Rainfall_mm': [rainfall],
        'Temperature_Celsius': [temperature],
        'Fertilizer_Used': [fertilizer],
        'Irrigation_Used': [irrigation],
        'Weather_Condition': [weather],
        'Days_to_Harvest': [days]
    })

    test_pool = Pool(
        input_data,
        cat_features=['Region','Soil_Type','Crop', 'Fertilizer_Used','Irrigation_Used','Weather_Condition']
    )

    prediction = model.predict(test_pool)[0]
    logger.info(f"🎯 CatBoost prediction result: {prediction:.2f}")
    return prediction

@app.post("/api/refined-prediction")
async def get_refined_prediction(request: RefinedPredictionRequest):
    """
    Endpoint для уточненного прогноза (альтернативное имя для совместимости)
    """
    return await get_refined_yield(request)

@app.post("/api/refined-yield")
async def get_refined_yield(request: RefinedPredictionRequest):
    """
    Основной endpoint для уточненного прогноза
    """
    logger.info(f"📥 Received refined prediction request for crop: '{request.crop_name}', region: '{request.region}'")
    logger.info(f"📊 Request details: field_area={request.field_area}, base_yield={request.base_yield}")
    logger.info(f"🔧 Refined params: soil_type={request.soil_type}, rainfall={request.rainfall_mm}mm, temp={request.temperature_celsius}°C")
    logger.info(f"🔧 Refined params: fertilizer={request.fertilizer_used}, irrigation={request.irrigation_used}")
    logger.info(f"🔧 Refined params: weather={request.weather_condition}, days={request.days_to_harvest}")
    
    if catboost_model is None:
        logger.error("❌ CatBoost model is not loaded")
        raise HTTPException(status_code=500, detail="CatBoost model not loaded")
    
    try:
        # Подготавливаем параметры для преобразования
        params_to_transform = {
            'region': request.region,
            'soil_type': request.soil_type,
            'crop': request.crop_name,
            'rainfall': request.rainfall_mm,
            'temperature': request.temperature_celsius,
            'fertilizer': request.fertilizer_used,
            'irrigation': request.irrigation_used,
            'weather': request.weather_condition,
            'days': request.days_to_harvest
        }
        
        # Преобразуем русские названия в английские
        transformed_params = transform_russian_to_english(params_to_transform)
        
        logger.info(f"🔄 Transformed params for CatBoost:")
        logger.info(f"  - Region: {params_to_transform['region']} -> {transformed_params['region']}")
        logger.info(f"  - Soil Type: {params_to_transform['soil_type']} -> {transformed_params['soil_type']}")
        logger.info(f"  - Crop: {params_to_transform['crop']} -> {transformed_params['crop']}")
        logger.info(f"  - Weather: {params_to_transform['weather']} -> {transformed_params['weather']}")
        logger.info(f"  - Fertilizer: {params_to_transform['fertilizer']} -> {transformed_params['fertilizer']}")
        logger.info(f"  - Irrigation: {params_to_transform['irrigation']} -> {transformed_params['irrigation']}")
        
        prediction = catboost_predict(
            model=catboost_model,
            region=transformed_params['region'],
            soil_type=transformed_params['soil_type'],
            crop=transformed_params['crop'],
            rainfall=transformed_params['rainfall'],
            temperature=transformed_params['temperature'],
            fertilizer=transformed_params['fertilizer'],
            irrigation=transformed_params['irrigation'],
            weather=transformed_params['weather'],
            days=transformed_params['days']
        )
        
        response_data = {
            "refined_yield": float(prediction),
            "crop": request.crop_name,
            "region": request.region,
            "field_area": request.field_area,
            "base_yield": request.base_yield,
            "status": "success"
        }
        logger.info(f"📤 Sending refined prediction: {prediction:.2f}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error in refined prediction: {str(e)}")
        logger.error(f"📝 Stack trace: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")