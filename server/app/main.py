from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear todas las tablas (temporal, luego usaremos Alembic)
Base.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Drone Delivery Platform API",
    description="API para plataforma de entrega con drones",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint de prueba "Hola Mundo"
@app.get("/")
async def root():
    return {"message": "¡Hola Mundo! Drone Delivery Platform API está funcionando"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Drone Delivery API está operativa",
        "version": "1.0.0"
    }

# Incluir rutas de la API cuando estén listas
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )