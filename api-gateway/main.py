import logging
import os
import uuid
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="API Gateway", description="Центральный шлюз системы микроклимата")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация портов из твоего плана
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
    "core": os.getenv("CORE_SERVICE_URL", "http://core-service:8002"),
    "data": os.getenv("DATA_SERVICE_URL", "http://data-storage-service:8003"),
    "sensors": os.getenv("SENSORS_SERVICE_URL", "http://sensor-ingestion-service:8004"),
    "ml": os.getenv("ML_SERVICE_URL", "http://ml-prediction-service:8005"),
    "rooms": os.getenv("ROOMS_SERVICE_URL", "http://room-management-service:8006"),
    "notifications": os.getenv("NOTIFICATIONS_SERVICE_URL", "http://notification-service:8007"),
    "events": os.getenv("EVENTS_SERVICE_URL", "http://event-log-service:8008"),
    "files": os.getenv("FILES_SERVICE_URL", "http://minio-file-service:8009"),
}

# Список путей, которые НЕ ТРЕБУЮТ проверки токена
PUBLIC_ROUTES = [
    "/auth/login",
    "/auth/register",
    "/docs",            # Документация шлюза
    "/openapi.json",    # Схема API шлюза
    "/health"           # Проверка работоспособности
]

async_client = httpx.AsyncClient()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Добавляет Request-ID для сквозной трассировки запросов.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

async def check_auth(request: Request):
    """
    Проверка прав доступа. Пропускает публичные запросы без проверки токена.
    """
    path = request.url.path
    
    # 1. Проверяем, не является ли путь публичным
    if any(path.startswith(route) for route in PUBLIC_ROUTES):
        return

    # 2. Если путь защищенный, проверяем наличие заголовка
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning(f"Unauthorized access attempt to {path}")
        raise HTTPException(status_code=401, detail="Отсутствует заголовок Authorization")

    # 3. Делегируем проверку в auth-service (Порт: 8001)
    try:
        # Прокидываем Request-ID для логов
        headers = {"Authorization": auth_header, "X-Request-ID": request.headers.get("X-Request-ID", "")}
        
        verify_res = await async_client.get(
            f"{SERVICES['auth']}/auth/verify", 
            headers=headers,
            timeout=2.0
        )
        if verify_res.status_code != 200:
            raise HTTPException(status_code=401, detail="Токен не валиден")
            
    except httpx.RequestError:
        logger.error("Сервис авторизации недоступен")
        raise HTTPException(status_code=503, detail="Ошибка проверки прав доступа")

@app.api_route("/{service}/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@limiter.limit("30/minute") # Увеличил лимит для комфортной работы фронта
async def gateway_proxy(service: str, rest_of_path: str, request: Request, _ = Depends(check_auth)):
    """
    Универсальное проксирование всех запросов.
    """
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Микросервис не найден")

    # Формируем целевой URL. Например: /auth/login -> http://localhost:8001/auth/login
    target_url = f"{SERVICES[service]}/{service}/{rest_of_path}"
    
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None) # httpx сам пересчитает длину
    headers["X-Request-ID"] = request.headers.get("X-Request-ID", "")

    try:
        req = async_client.build_request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body(),
            params=request.query_params,
            timeout=30.0
        )
        response = await async_client.send(req, stream=True)
        
        return StreamingResponse(
            response.aiter_raw(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except httpx.RequestError as exc:
        logger.error(f"Ошибка проксирования в {service}: {exc}")
        raise HTTPException(status_code=502, detail=f"Сервис {service} временно недоступен")

@app.on_event("shutdown")
async def shutdown():
    await async_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)