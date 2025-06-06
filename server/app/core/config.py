from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import json
from functools import lru_cache

class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_TEST_URL: Optional[str] = None
    
    # Seguridad
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS - Puede ser string JSON o lista
    CORS_ORIGINS: Union[List[str], str] = '["http://localhost:3000", "http://127.0.0.1:3000"]'
    
    # Configuración de la aplicación
    PROJECT_NAME: str = "Drone Delivery Platform"
    VERSION: str = "1.0.0"
    PROJECT_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    
    # Configuración de drones
    DEFAULT_DRONE_SPEED: int = 50  # km/h
    DEFAULT_DRONE_RANGE: int = 10000  # metros
    SERVICE_COST_PER_KM: float = 2.5  # costo por kilómetro
    SERVICE_COST_AFTER_HOUR_PER_KM: float = 5.0  # costo por kilómetro después de la primera hora
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte CORS_ORIGINS a lista si es string JSON"""
        if isinstance(self.CORS_ORIGINS, str):
            try:
                return json.loads(self.CORS_ORIGINS)
            except json.JSONDecodeError:
                # Si no es JSON válido, dividir por comas
                return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construir DATABASE_TEST_URL si no está definida
        if not self.DATABASE_TEST_URL:
            if "postgresql+psycopg" in self.DATABASE_URL:
                self.DATABASE_TEST_URL = self.DATABASE_URL.replace(self.DB_NAME, f"{self.DB_NAME}_test")
            else:
                self.DATABASE_TEST_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}_test"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Permitir variables extra sin errores
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()