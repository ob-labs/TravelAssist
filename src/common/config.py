"""
Application configuration for TravelAssist.

Centralized configuration loaded from environment variables.
All default values are defined here; only this module may call
dotenv.load_dotenv().

Config is a singleton; use get_config() to obtain the global instance.
Database settings are accessed via get_config().database_config.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import dotenv

dotenv.load_dotenv()

# Default values (aligned with .env.example and application defaults)
_DEFAULT_DB_HOST = "127.0.0.1"
_DEFAULT_DB_PORT = "2881"
_DEFAULT_DB_USER = "root"
_DEFAULT_DB_PASSWORD = "your-password"
_DEFAULT_DB_NAME = "test"
_DEFAULT_DB_SSL_CA_PATH = ""
_DEFAULT_DASHSCOPE_API_KEY = ""
_DEFAULT_AMAP_API_KEY = ""
_DEFAULT_LLM_MODEL = "qwen-plus"
_DEFAULT_LLM_TOP_P = 0.1
_DEFAULT_LLM_TEMPERATURE = 0.3
_DEFAULT_TABLE_NAME = "travel_assist"
_DEFAULT_TOPK = 20
_DEFAULT_MAX_WORKERS = 8
_DEFAULT_RETRY_COUNT = 3


@dataclass
class DatabaseConfig:
    """
    Database connection configuration.

    Supports both new DB_* and legacy OB_* environment variables
    for backward compatibility.
    """

    host: str
    port: str
    user: str
    password: str
    database: str
    ssl_ca_path: Optional[str] = None

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Build DatabaseConfig from environment variables."""
        def _str(val: str) -> str:
            return (val or "").strip().strip('"')

        return cls(
            host=_str(os.getenv("DB_HOST", _DEFAULT_DB_HOST)),
            port=_str(os.getenv("DB_PORT", _DEFAULT_DB_PORT)),
            user=_str(os.getenv("DB_USER", _DEFAULT_DB_USER)),
            password=_str(os.getenv("DB_PASSWORD", _DEFAULT_DB_PASSWORD)),
            database=_str(os.getenv("DB_NAME", _DEFAULT_DB_NAME)),
            ssl_ca_path=_str(
                os.getenv("DB_SSL_CA_PATH", _DEFAULT_DB_SSL_CA_PATH)
            ) or None,
        )

    @property
    def uri(self) -> str:
        """Get the database URI in host:port format."""
        return f"{self.host}:{self.port}"

    def get_connect_args(self) -> Optional[Dict[str, Any]]:
        """
        Get SSL connection arguments if SSL is configured.

        Returns:
            SSL connection arguments dict, or None if SSL is not configured.
        """
        if not self.ssl_ca_path:
            return None
        return {
            "ssl": {
                "ca": self.ssl_ca_path,
                "check_hostname": False,
            }
        }


@dataclass
class Config:
    """
    Application configuration loaded from environment variables.

    Single instance per process; obtain via get_config().
    All API keys and sensitive configuration should be stored
    in environment variables and accessed through this class.
    """

    # API Keys
    dashscope_api_key: Optional[str] = None
    amap_api_key: Optional[str] = None

    # LLM Settings
    default_llm_model: str = _DEFAULT_LLM_MODEL
    llm_top_p: float = _DEFAULT_LLM_TOP_P
    llm_temperature: float = _DEFAULT_LLM_TEMPERATURE

    # Database: use member database_config (DatabaseConfig) for connection settings
    database_config: Optional[DatabaseConfig] = None

    # Database Query Settings (table name, topk for app logic)
    default_table_name: str = _DEFAULT_TABLE_NAME
    default_topk: int = _DEFAULT_TOPK

    # Async Settings
    max_workers: int = _DEFAULT_MAX_WORKERS
    default_retry_count: int = _DEFAULT_RETRY_COUNT

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create Config from environment variables.

        Returns:
            A new Config instance with values from environment.
        """
        dashscope_key = os.getenv("DASHSCOPE_API_KEY", _DEFAULT_DASHSCOPE_API_KEY)
        amap_key = os.getenv("AMAP_API_KEY", _DEFAULT_AMAP_API_KEY)
        return cls(
            dashscope_api_key=dashscope_key or None,
            amap_api_key=amap_key or None,
            default_llm_model=os.getenv("LLM_MODEL", _DEFAULT_LLM_MODEL),
            llm_top_p=float(os.getenv("LLM_TOP_P", str(_DEFAULT_LLM_TOP_P))),
            llm_temperature=float(
                os.getenv("LLM_TEMPERATURE", str(_DEFAULT_LLM_TEMPERATURE))
            ),
            database_config=DatabaseConfig.from_env(),
            default_table_name=os.getenv("TABLE_NAME", _DEFAULT_TABLE_NAME),
            default_topk=int(os.getenv("TOPK", str(_DEFAULT_TOPK))),
            max_workers=int(os.getenv("MAX_WORKERS", str(_DEFAULT_MAX_WORKERS))),
            default_retry_count=int(
                os.getenv("RETRY_COUNT", str(_DEFAULT_RETRY_COUNT))
            ),
        )

    def validate(self) -> None:
        """
        Validate that required settings are configured.

        Raises:
            ValueError: If required settings are missing.
        """
        if not self.dashscope_api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY environment variable is required"
            )
        if not self.amap_api_key:
            raise ValueError(
                "AMAP_API_KEY environment variable is required"
            )


# Global singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global singleton Config instance.

    Returns:
        The application Config instance. Database config via .database_config.
    """
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config
