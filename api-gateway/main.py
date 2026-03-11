import logging
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
    "auth": "http://localhost:8001",
    "core": "http://localhost:8002",  # Проверка: Core Service на порту 8002
    "data": "http://localhost:8003",
    "sensors": "http://localhost:8004",
    "ml": "http://localhost:8005",
    "rooms": "http://localhost:8006",
    "notifications": "http://localhost:8007",
    "events": "http://localhost:8008",
    "files": "http://localhost:8009",
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
        verify_res = await async_client.get(
            f"{SERVICES['auth']}/auth/verify", 
            headers={"Authorization": auth_header},
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