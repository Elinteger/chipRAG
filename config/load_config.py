from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- PostgreSQL / Database ---
    postgre_username: str = Field(..., alias="USERNAME")
    postgre_password: str = Field(..., alias="USER_PASSWORD")
    postgre_database_name: str = Field(..., alias="DATABASE_NAME")
    postgre_host: str = Field(..., alias="HOST_URL")
    postgre_port: int = Field(..., alias="PORT")

    # --- Kipitz / OpenAI API ---
    kipitz_api_token: str = Field(..., alias="KIPITZ_API_TOKEN")
    kipitz_base_url: str = Field(..., alias="BASE_URL")
    kipitz_model: str = Field(..., alias="MODEL")
    kipitz_role: str = Field(..., alias="ROLE")

    # --- Paths ---
    prompt_path: str = Field(..., alias="PROMPT_PATH")
    query_path: str = Field(..., alias="QUERY_PATH")

    class Config:
        env_file = ".env"
        case_sensitive = True
    
settings = Settings()
