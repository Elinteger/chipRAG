import json
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings
from typing import List, Dict

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
    kipit_role: str = Field(..., alias="ROLE")

    # --- Paths ---
    prompt_path: str = Field(..., alias="PROMPT_PATH")
    query_path: str = Field(..., alias="QUERY_PATH")

    # --- EU Data Fetcher ---
    eu_api_endpoint: str = Field(..., alias="EU_API_ENDPOINT")
    headers: Dict[str, str] = Field(..., alias="HEADERS")
    eu_api_output_format: str = Field(..., alias="OUTPUT_FORMAT")
    eu_api_output_language: str = Field(..., alias="OUTPUT_LANGUAGE")

    # --- EU Data Cleaning ---
    columns_to_keep: List[str] = Field(..., alias="COLUMNS_TO_KEEP")


    class Config:
        env_file = ".env"
        case_sensitive = True

    # --- Validators/Parsers ---
    @field_validator("columns_to_keep", mode="before")
    def parse_columns_to_keep(cls, v):
        # Expecting a JSON-like list in .env, parse it
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON for COLUMNS_TO_KEEP: {e}")
        return v

    #FIXME: dont know if '' is actually wrong and "" is needed, hasnt been like that before -> test!
    @field_validator("headers", mode="before")
    def parse_headers(cls, v):
        # Fix single quotes to double quotes and parse dict string from .env
        if isinstance(v, str):
            try:
                # Replace single quotes with double quotes for valid JSON
                v_fixed = v.replace("'", '"')
                return json.loads(v_fixed)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON for HEADERS: {e}")
        return v
    
    @field_validator("eu_api_output_language", mode="before")
    def upcase_output_language(cls, v):
        # Optionally restrict language to known options
        return v.upper()
    
settings = Settings()
