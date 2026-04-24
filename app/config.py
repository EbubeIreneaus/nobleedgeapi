from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Noble Edge ROI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_PORT: int
    DB_URL: str

    # Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    ADMIN_EMAIL: str

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Crypto wallet addresses (admin-owned)
    BTC_WALLET: str
    USDT_TRC20_WALLET: str
    USDT_ERC20_WALLET: str
    ETH_WALLET: str

    # Referral
    REFERRAL_BONUS_PERCENT: float = 5.0  # % of referee's first deposit

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
