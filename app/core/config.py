

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
   
    APP_DATABASE_URL: str = ""  

    
    DATABASE_URL_DIRECT: str = ""  

    JWT_SECRET_KEY: str = ""  
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

  
    FRONTEND_ORIGIN: str = "https://voice-guard-pay.vercel.app" 

    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
