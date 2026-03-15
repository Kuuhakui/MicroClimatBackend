import os
import psycopg2
from psycopg2 import pool
from fastapi import FastAPI, HTTPException, Header, APIRouter
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from auth_utils import hash_password, verify_password, create_access_token, ALGORITHM, SECRET_KEY
from jose import jwt, JWTError

load_dotenv()

app = FastAPI(title="MicroClimat Auth Service")
# Создаем роутер с префиксом, чтобы шлюз мог корректно перенаправлять запросы
auth_router = APIRouter(prefix="/auth", tags=["Auth"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Работа с БД (Connection Pool) ---
db_pool = None

@app.on_event("startup")
def startup_db_pool():
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT")
        )
        print("✅ Пул соединений с БД успешно создан")
        _init_schema()
    except Exception as e:
        print(f"❌ Ошибка создания пула БД: {e}")

def _init_schema():
    """Создаёт таблицы и заполняет справочники, если они пустые."""
    conn = db_pool.getconn()
    cur = conn.cursor()
    try:
        # Создаём таблицы, если не существуют
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL
            );
            CREATE EXTENSION IF NOT EXISTS "pgcrypto";
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role_id INTEGER NOT NULL REFERENCES roles(id),
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id UUID PRIMARY KEY REFERENCES users(id),
                theme VARCHAR(20) DEFAULT 'light',
                language VARCHAR(5) DEFAULT 'ru',
                notifications_enabled BOOLEAN DEFAULT TRUE
            );
        """)
        # Гарантируем DEFAULT значения (на случай если таблица создана другим сервисом)
        cur.execute("""
            ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid();
            ALTER TABLE users ALTER COLUMN created_at SET DEFAULT NOW();
            ALTER TABLE user_preferences ALTER COLUMN theme SET DEFAULT 'light';
            ALTER TABLE user_preferences ALTER COLUMN language SET DEFAULT 'ru';
            ALTER TABLE user_preferences ALTER COLUMN notifications_enabled SET DEFAULT TRUE;
        """)
        # Заполняем роли, если пусто
        cur.execute("SELECT COUNT(*) FROM roles")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO roles (name) VALUES ('admin'), ('operator'), ('viewer')")
            print("✅ Роли созданы: admin, operator, viewer")
        conn.commit()
        print("✅ Схема БД инициализирована")
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка инициализации схемы: {e}")
    finally:
        cur.close()
        db_pool.putconn(conn)

@app.on_event("shutdown")
def close_db_pool():
    if db_pool:
        db_pool.closeall()
        print("🛑 Пул соединений с БД закрыт")

def get_db_conn():
    if not db_pool:
        raise HTTPException(status_code=503, detail="DB Pool not initialized")
    return db_pool.getconn()

# --- Схемы данных ---
class UserRegister(BaseModel):
    username: str
    password: str
    role_name: str = "operator"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Эндпоинты внутри роутера ---

@auth_router.post("/register", status_code=201)
def register(user: UserRegister):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        hashed_pw = hash_password(user.password)
        cur.execute("SELECT id FROM roles WHERE name = %s", (user.role_name,))
        role_res = cur.fetchone()
        if not role_res:
            raise HTTPException(status_code=400, detail=f"Роль '{user.role_name}' не найдена. Доступные: admin, operator, viewer")
        
        # Вставляем пользователя
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s) RETURNING id",
                (user.username, hashed_pw, role_res[0])
            )
        except psycopg2.IntegrityError:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Пользователь уже существует")
        
        user_id = cur.fetchone()[0]
        print(f"✅ User created: {user.username}, id={user_id}, type={type(user_id)}")
        
        # Вставляем preferences — отдельный try чтобы отличить от ошибки Users
        try:
            cur.execute("INSERT INTO user_preferences (user_id) VALUES (%s)", (str(user_id),))
        except Exception as pref_err:
            print(f"⚠️  user_preferences insert failed: {pref_err} (user_id={user_id})")
            # Продолжаем без preferences — не критично
            conn.rollback()
            conn.autocommit = False
            cur.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s) RETURNING id",
                (user.username, hashed_pw, role_res[0])
            )
            user_id = cur.fetchone()[0]
        
        conn.commit()
        return {"message": "User created", "id": str(user_id)}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"❌ Register error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка регистрации: {str(e)}")
    finally:
        cur.close()
        db_pool.putconn(conn)

@auth_router.post("/login", response_model=Token) # Переименовали для шлюза
def login(user: UserLogin):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.password_hash, r.name 
        FROM users u 
        JOIN roles r ON u.role_id = r.id 
        WHERE u.username = %s
    """, (user.username,))
    res = cur.fetchone()
    cur.close()
    db_pool.putconn(conn)

    if not res or not verify_password(user.password, res[1]): # Используем утилиту
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    # Используем твою функцию генерации токена
    token = create_access_token(data={
        "sub": str(res[0]), 
        "username": user.username,
        "role": res[2]
    })
    
    return {"access_token": token, "token_type": "bearer"}

@auth_router.get("/verify")
def verify_token(authorization: str = Header(None)):
    """Эндпоинт, который вызывает API Gateway для проверки прав"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен отсутствует")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "status": "valid",
            "user": {
                "id": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role")
            }
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Токен недействителен")

# Подключаем роутер к приложению
app.include_router(auth_router)