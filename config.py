from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    VIEWDNS_API_KEY: str
    database_url: str
    smtp_server: str
    smtp_port: str
    smtp_user: str
    smtp_pass: str
    email_from: str
    email_to: str

    class Config:
        env_file = ".env"

settings = Settings()
VIEWDNS_API_KEY = settings.VIEWDNS_API_KEY
