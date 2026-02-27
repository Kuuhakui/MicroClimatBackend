import pandas as pd
import requests
import time
from tqdm import tqdm
import os

# Координаты Трёхгорного (Челябинская область)
LAT = 54.81
LON = 58.45
START_YEAR = 2020
END_YEAR = 2025 
OUTPUT_FILE = "data/real_weather_trekhgorny_5years.csv"

def fetch_month_data(year, month):
    start_date = f"{year}-{month:02d}-01"
    # Определяем последний день месяца
    if month in [4, 6, 9, 11]: last_day = 30
    elif month == 2: 
        last_day = 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28
    else: last_day = 31
    end_date = f"{year}-{month:02d}-{last_day}"
    
    # Запрашиваем архивные данные: температуру, влажность, осадки и облачность
    url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={LAT}&longitude={LON}"
           f"&start_date={start_date}&end_date={end_date}"
           f"&hourly=temperature_2m,relative_humidity_2m,precipitation,cloud_cover&timezone=auto")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get('hourly', {})
        if not hourly: return None
        
        df_month = pd.DataFrame({
            "timestamp": pd.to_datetime(hourly.get('time')),
            "temp_outdoor": hourly.get('temperature_2m'),
            "humidity": hourly.get('relative_humidity_2m'),
            "precipitation": hourly.get('precipitation'),
            "cloud_cover": hourly.get('cloud_cover')
        })
        return df_month
    except Exception as e:
        print(f"\n Ошибка ({year}-{month:02d}): {e}")
        return None

# --- Основной процесс ---
os.makedirs("data", exist_ok=True)
all_data = []

print(f"--- Загрузка архива погоды Open-Meteo за {START_YEAR}-{END_YEAR} гг. ---")

total_months = (END_YEAR - START_YEAR + 1) * 12
with tqdm(total=total_months, desc="Общий прогресс") as pbar:
    for year in range(START_YEAR, END_YEAR + 1):
        for month in range(1, 13):
            # Если 2025 год еще не закончился, можно добавить проверку на текущую дату, 
            # но архив обычно отдает данные до вчерашнего дня.
            df_m = fetch_month_data(year, month)
            if df_m is not None:
                all_data.append(df_m)
            pbar.update(1)
            time.sleep(0.5) # Пауза, чтобы не нагружать бесплатный API

if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df['timestamp'] = final_df['timestamp'].dt.tz_localize(None)
    
    # Удаляем возможные дубликаты и пустые строки
    final_df.drop_duplicates(subset=['timestamp'], inplace=True)
    final_df.dropna(subset=['temp_outdoor'], inplace=True)
    
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n Готово! Файл сохранен: {OUTPUT_FILE}")
    print(f" Итого записей: {len(final_df)}")
    print(f" Период: {final_df['timestamp'].min()} ---> {final_df['timestamp'].max()}")
else:
    print("\n Данные не получены.")