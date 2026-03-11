import os
import subprocess
import time
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

def run_command(command):
    """Утилита для запуска системных команд."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Ошибка: {result.stderr}")
        return False
    return True

def setup_database():
    print("🛠️  Инициализация окружения...")
    
    # 1. Запуск Docker Compose
    print("🐳 Запуск Docker контейнеров...")
    if run_command("docker-compose up -d"):
        print("✅ Контейнеры запущены.")
    else:
        return

    # 2. Ожидание готовности БД
    container_name = os.getenv("CONTAINER_NAME")
    db_user = os.getenv("DB_USER")
    
    print(f"⏳ Ждем, пока {container_name} будет готов принимать соединения...")
    
    retries = 10
    while retries > 0:
        check = subprocess.run(
            f"docker exec {container_name} pg_isready -U {db_user}", 
            shell=True, capture_output=True
        )
        if check.returncode == 0:
            print("🚀 База данных готова к работе!")
            break
        retries -= 1
        time.sleep(2)
    else:
        print("❌ Не удалось дождаться запуска базы.")
        return

    print("-" * 30)
    print(f"Данные подключения:")
    print(f"Host: localhost")
    print(f"Port: {os.getenv('DB_PORT')}")
    print(f"DB:   {os.getenv('DB_NAME')}")
    print(f"User: {os.getenv('DB_USER')}")
    print("-" * 30)

if __name__ == "__main__":
    setup_database()