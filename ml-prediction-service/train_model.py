import pandas as pd
import numpy as np
import os
import joblib
import matplotlib.pyplot as plt
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# --- Конфигурация ---
DATA_FILE = "data/real_weather_trekhgorny_5years.csv"
MODEL_DIR = "models"
MODEL_FILENAME = "xgboost_final_5y.pkl"

# Все параметры, которые теперь есть в данных
FEATURES = [
    'temp_outdoor', 'humidity', 'precipitation', 'cloud_cover', 
    'temp_lag_1h', 'temp_diff', 'temp_roll_mean_6h', 
    'temp_sin', 'temp_cos'
]
TARGET = 'target_temp_plus_1h'

os.makedirs(MODEL_DIR, exist_ok=True)

# --- 1. Загрузка и инженерия признаков ---
print(f"Загрузка данных: {DATA_FILE}")
df = pd.read_csv(DATA_FILE)
df['timestamp'] = pd.to_datetime(df['timestamp'])

print("Создание дополнительных признаков...")
# Временные циклы
df['hour'] = df['timestamp'].dt.hour
df['temp_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['temp_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

# Инженерные признаки (лаги и скользящие средние)
df['temp_lag_1h'] = df['temp_outdoor'].shift(1)
df['temp_diff'] = df['temp_outdoor'] - df['temp_lag_1h']
df['temp_roll_mean_6h'] = df['temp_outdoor'].rolling(window=6).mean()

# Цель: температура через час
df['target_temp_plus_1h'] = df['temp_outdoor'].shift(-1)

# Удаляем пустые строки, возникшие из-за сдвигов
df.dropna(inplace=True)

# --- 2. Разделение данных по времени ---
# Обучаем на всем до 2025 года, тестируем на 2025-м
train_df = df[df['timestamp'] < '2025-01-01']
test_df = df[df['timestamp'] >= '2025-01-01']

X_train, y_train = train_df[FEATURES], train_df[TARGET]
X_test, y_test = test_df[FEATURES], test_df[TARGET]

print(f"\nВыборки сформированы:")
print(f" - Обучение (2020-2024): {len(X_train)} строк")
print(f" - Тест (2025): {len(X_test)} строк")

# --- 3. Обучение модели ---
print("\nЗапуск обучения XGBoost (это может занять полминуты)...")
model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    n_jobs=-1,
    random_state=42
)

model.fit(X_train, y_train)

# --- 4. Тестирование и метрики ---
y_pred = model.predict(X_test)

rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"\n--- Итоговые метрики за весь 2025 год ---")
print(f"Средняя ошибка (MAE): {mae:.4f} °C")
print(f"Квадратичная ошибка (RMSE): {rmse:.4f} °C")
print(f"Точность (R^2 Score): {r2:.4f}")

# --- 5. Анализ важности признаков ---
importance = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print("\nВажность признаков:")
print(importance)

# Сохранение
joblib.dump(model, os.path.join(MODEL_DIR, MODEL_FILENAME))

# --- 6. Визуализация (последняя неделя декабря 2025 для примера) ---
plt.figure(figsize=(15, 6))
last_days = test_df.tail(168) # Последняя неделя
plt.plot(last_days['timestamp'], y_test.tail(168), label='Реальность (Трёхгорный)', color='#2980b9')
plt.plot(last_days['timestamp'], y_pred[-168:], label='Прогноз системы', color='#c0392b', linestyle='--')
plt.title('Проверка точности модели на финальном тесте (декабрь 2025)')
plt.ylabel('Температура (°C)')
plt.grid(True, alpha=0.3)
plt.legend()
plt.show()