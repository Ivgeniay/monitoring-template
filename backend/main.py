from litestar import Litestar, get, post
from litestar.response import Response
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins.prometheus import PrometheusConfig
from litestar.config.cors import CORSConfig
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry, REGISTRY
import time
import random
import asyncio

registry = CollectorRegistry()

REQUEST_COUNT = Counter('http_requests_total', 'Общее количество HTTP запросов', ['method', 'endpoint'], registry=registry)
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Время выполнения HTTP запросов', ['method', 'endpoint'], registry=registry)
ACTIVE_USERS = Gauge('active_users_total', 'Количество активных пользователей', registry=registry)

@get("/")
async def index() -> dict:
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    
    with REQUEST_DURATION.labels(method='GET', endpoint='/').time():
        await simulate_work()
    
    return {"message": "Привет от Litestar!"}

@get("/users")
async def get_users() -> dict:
    REQUEST_COUNT.labels(method='GET', endpoint='/users').inc()
    
    with REQUEST_DURATION.labels(method='GET', endpoint='/users').time():
        await simulate_work()
        
    ACTIVE_USERS.set(random.randint(10, 100))
    
    return {"users": ["Алексей", "Мария", "Дмитрий"]}

@post("/users")
async def create_user(data: dict) -> dict:
    REQUEST_COUNT.labels(method='POST', endpoint='/users').inc()
    
    with REQUEST_DURATION.labels(method='POST', endpoint='/users').time():
        await simulate_work()
    
    return {"message": "Пользователь создан", "user": data}

@get("/health")
async def health() -> dict:
    REQUEST_COUNT.labels(method='GET', endpoint='/health').inc()
    return {"status": "ok", "timestamp": int(time.time())}

@get("/metrics")
async def metrics() -> Response:
    return Response(
        content=generate_latest(registry).decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )

async def simulate_work():
    await asyncio.sleep(random.uniform(0.01, 0.1))

prometheus_config = PrometheusConfig();
cors_config = CORSConfig(
    allow_origins=["http://localhost:8080"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
openApi = OpenAPIConfig(
    title="Бек",
    description="desc",
    version="0.0.1",
    path="/docs",
    render_plugins=[ScalarRenderPlugin()]
);

app = Litestar(
    route_handlers=[index, get_users, create_user, health, metrics],
    middleware=[prometheus_config.middleware],
    openapi_config=openApi,
    cors_config=cors_config
)

if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )