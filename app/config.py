"""
Unified IPTV AceStream Platform Configuration
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Any
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carica prima .env.example come base, poi .env per sovrascrivere
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_EXAMPLE_PATH = BASE_DIR / ".env.example"
ENV_PATH = BASE_DIR / ".env"

# Carica prima i default da .env.example
if ENV_EXAMPLE_PATH.exists():
    load_dotenv(ENV_EXAMPLE_PATH)
    logger.info(f"Loaded default configuration from {ENV_EXAMPLE_PATH}")
else:
    logger.warning(f".env.example not found at {ENV_EXAMPLE_PATH}")

# Poi sovrascrivi con .env se esiste
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
    logger.info(f"Loaded custom configuration from {ENV_PATH}")
else:
    logger.info(".env file not found, using defaults from .env.example")


class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    pass


class Config:
    """Configuration class for the application"""
    
    @staticmethod
    def _get_env(key: str, required: bool = False, default: Any = None) -> Optional[str]:
        """
        Safely get environment variable with error handling
        
        Args:
            key: Environment variable name
            required: Whether the variable is required
            default: Default value if not found
            
        Returns:
            Environment variable value or default
            
        Raises:
            ConfigurationError: If required variable is missing
        """
        value = os.getenv(key, default)
        if required and value is None:
            raise ConfigurationError(f"Required environment variable '{key}' is not set")
        return value
    
    @staticmethod
    def _parse_int(key: str, default: Optional[int] = None, required: bool = False, 
                   min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
        """
        Parse integer with validation
        
        Args:
            key: Environment variable name
            default: Default value
            required: Whether the variable is required
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Parsed integer value
            
        Raises:
            ConfigurationError: If parsing fails or validation fails
        """
        value_str = Config._get_env(key, required=required)
        if value_str is None:
            if default is not None:
                return default
            raise ConfigurationError(f"No value provided for '{key}' and no default available")
        
        try:
            value = int(value_str)
        except (ValueError, TypeError) as e:
            raise ConfigurationError(f"Invalid integer value for '{key}': {value_str}") from e
        
        if min_value is not None and value < min_value:
            raise ConfigurationError(f"Value for '{key}' ({value}) is less than minimum ({min_value})")
        
        if max_value is not None and value > max_value:
            raise ConfigurationError(f"Value for '{key}' ({value}) is greater than maximum ({max_value})")
        
        return value
    
    @staticmethod
    def _parse_float(key: str, default: Optional[float] = None, required: bool = False,
                    min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
        """
        Parse float with validation
        
        Args:
            key: Environment variable name
            default: Default value
            required: Whether the variable is required
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            Parsed float value
            
        Raises:
            ConfigurationError: If parsing fails or validation fails
        """
        value_str = Config._get_env(key, required=required)
        if value_str is None:
            if default is not None:
                return default
            raise ConfigurationError(f"No value provided for '{key}' and no default available")
        
        try:
            value = float(value_str)
        except (ValueError, TypeError) as e:
            raise ConfigurationError(f"Invalid float value for '{key}': {value_str}") from e
        
        if min_value is not None and value < min_value:
            raise ConfigurationError(f"Value for '{key}' ({value}) is less than minimum ({min_value})")
        
        if max_value is not None and value > max_value:
            raise ConfigurationError(f"Value for '{key}' ({value}) is greater than maximum ({max_value})")
        
        return value
    
    @staticmethod
    def _parse_bool(key: str, default: bool = False, required: bool = False) -> bool:
        """
        Parse boolean with validation
        
        Args:
            key: Environment variable name
            default: Default value
            required: Whether the variable is required
            
        Returns:
            Parsed boolean value
            
        Raises:
            ConfigurationError: If parsing fails
        """
        value_str = Config._get_env(key, required=required)
        if value_str is None:
            return default
        
        value_lower = value_str.lower().strip()
        if value_lower in ('true', '1', 'yes', 'on', 'enabled'):
            return True
        elif value_lower in ('false', '0', 'no', 'off', 'disabled', ''):
            return False
        else:
            raise ConfigurationError(f"Invalid boolean value for '{key}': {value_str}")
    
    @staticmethod
    def _parse_list(key: str, separator: str = ",", default: Optional[List[str]] = None,
                   required: bool = False, allow_empty: bool = True) -> List[str]:
        """
        Parse comma-separated list with validation
        
        Args:
            key: Environment variable name
            separator: Separator character
            default: Default value
            required: Whether the variable is required
            allow_empty: Whether empty lists are allowed
            
        Returns:
            Parsed list of strings
            
        Raises:
            ConfigurationError: If validation fails
        """
        value_str = Config._get_env(key, required=required)
        if value_str is None:
            if default is not None:
                return default
            return [] if allow_empty else None
        
        # Split and strip whitespace
        items = [item.strip() for item in value_str.split(separator) if item.strip()]
        
        if not allow_empty and not items:
            raise ConfigurationError(f"Empty list not allowed for '{key}'")
        
        return items
    
    # Server Configuration
    SERVER_HOST: str = None
    SERVER_PORT: int = None
    SERVER_TIMEZONE: str = None
    SERVER_DEBUG: bool = None
    
    # AceStream Configuration
    ACESTREAM_ENABLED: bool = None
    ACESTREAM_ENGINE_HOST: str = None
    ACESTREAM_ENGINE_PORT: int = None
    ACESTREAM_TIMEOUT: int = None
    
    # AceStream Streaming Server (internal)
    ACESTREAM_STREAMING_HOST: str = None
    ACESTREAM_STREAMING_PORT: int = None
    ACESTREAM_CHUNK_SIZE: int = None
    ACESTREAM_EMPTY_TIMEOUT: float = None
    ACESTREAM_NO_RESPONSE_TIMEOUT: float = None
    
    # Scraper Configuration
    SCRAPER_URLS: List[str] = None
    SCRAPER_UPDATE_INTERVAL: int = None
    
    # EPG Configuration
    EPG_SOURCES: List[str] = None
    EPG_UPDATE_INTERVAL: int = None
    EPG_CACHE_FILE: str = None
    
    # Database Configuration
    DATABASE_URL: str = None
    DATABASE_ECHO: bool = None
    DATABASE_POOL_SIZE: int = None
    DATABASE_MAX_OVERFLOW: int = None
    
    # Admin User
    ADMIN_USERNAME: str = None
    ADMIN_PASSWORD: str = None
    
    # Security
    SECRET_KEY: str = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = None
    
    @classmethod
    def load(cls):
        """Load configuration from environment variables"""
        # Server Configuration
        cls.SERVER_HOST = cls._get_env("SERVER_HOST", default="0.0.0.0")
        cls.SERVER_PORT = cls._parse_int("SERVER_PORT", default=6880, min_value=1, max_value=65535)
        cls.SERVER_TIMEZONE = cls._get_env("SERVER_TIMEZONE", default="Europe/Rome")
        cls.SERVER_DEBUG = cls._parse_bool("SERVER_DEBUG", default=False)
        
        # AceStream Configuration
        cls.ACESTREAM_ENABLED = cls._parse_bool("ACESTREAM_ENABLED", default=True)
        cls.ACESTREAM_ENGINE_HOST = cls._get_env("ACESTREAM_ENGINE_HOST", default="localhost")
        cls.ACESTREAM_ENGINE_PORT = cls._parse_int("ACESTREAM_ENGINE_PORT", default=6878, 
                                                     min_value=1, max_value=65535)
        cls.ACESTREAM_TIMEOUT = cls._parse_int("ACESTREAM_TIMEOUT", default=15, 
                                                min_value=1, max_value=300)
        
        # AceStream Streaming Server (internal)
        cls.ACESTREAM_STREAMING_HOST = cls._get_env("ACESTREAM_STREAMING_HOST", default="127.0.0.1")
        cls.ACESTREAM_STREAMING_PORT = cls._parse_int("ACESTREAM_STREAMING_PORT", default=6881,
                                                        min_value=1, max_value=65535)
        cls.ACESTREAM_CHUNK_SIZE = cls._parse_int("ACESTREAM_CHUNK_SIZE", default=8192,
                                                   min_value=1024, max_value=1048576)
        cls.ACESTREAM_EMPTY_TIMEOUT = cls._parse_float("ACESTREAM_EMPTY_TIMEOUT", default=60.0,
                                                        min_value=1.0, max_value=600.0)
        cls.ACESTREAM_NO_RESPONSE_TIMEOUT = cls._parse_float("ACESTREAM_NO_RESPONSE_TIMEOUT", 
                                                              default=10.0, min_value=1.0, max_value=60.0)
        
        # Scraper Configuration
        cls.SCRAPER_URLS = cls._parse_list("SCRAPER_URLS", default=[], allow_empty=True)
        cls.SCRAPER_UPDATE_INTERVAL = cls._parse_int("SCRAPER_UPDATE_INTERVAL", default=3600,
                                                      min_value=60, max_value=86400)
        
        # EPG Configuration
        cls.EPG_SOURCES = cls._parse_list("EPG_SOURCES", 
                                          default=["https://iptvx.one/EPG_NOARCH", "https://epg.pw/xmltv/epg.xml.gz"],
                                          allow_empty=True)
        cls.EPG_UPDATE_INTERVAL = cls._parse_int("EPG_UPDATE_INTERVAL", default=86400,
                                                  min_value=3600, max_value=604800)
        cls.EPG_CACHE_FILE = cls._get_env("EPG_CACHE_FILE", default="data/epg.xml")
        
        # Database Configuration
        cls.DATABASE_URL = cls._get_env("DATABASE_URL", default="sqlite:///data/unified-iptv.db")
        cls.DATABASE_ECHO = cls._parse_bool("DATABASE_ECHO", default=False)
        cls.DATABASE_POOL_SIZE = cls._parse_int("DATABASE_POOL_SIZE", default=10,
                                                 min_value=1, max_value=100)
        cls.DATABASE_MAX_OVERFLOW = cls._parse_int("DATABASE_MAX_OVERFLOW", default=20,
                                                    min_value=0, max_value=100)
        
        # Admin User
        cls.ADMIN_USERNAME = cls._get_env("ADMIN_USERNAME", default="admin")
        cls.ADMIN_PASSWORD = cls._get_env("ADMIN_PASSWORD", default="changeme")
        
        # Security
        cls.SECRET_KEY = cls._get_env("SECRET_KEY", default="change-this-secret-key-in-production")
        cls.ACCESS_TOKEN_EXPIRE_MINUTES = cls._parse_int("ACCESS_TOKEN_EXPIRE_MINUTES", default=43200,
                                                          min_value=1, max_value=525600)
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration with detailed checks
        
        Returns:
            True if validation passes
            
        Raises:
            ConfigurationError: If validation fails
        """
        validations = []
        
        # Check SECRET_KEY strength
        if len(cls.SECRET_KEY) < 32:
            validations.append("SECRET_KEY should be at least 32 characters long for security")
        
        if cls.SECRET_KEY == "change-this-secret-key-in-production":
            validations.append("SECRET_KEY is set to default value - CHANGE IT IN PRODUCTION!")
        
        # Check ADMIN_PASSWORD strength
        if len(cls.ADMIN_PASSWORD) < 8:
            validations.append("ADMIN_PASSWORD should be at least 8 characters long")
        
        if cls.ADMIN_PASSWORD == "changeme":
            validations.append("ADMIN_PASSWORD is set to default value - CHANGE IT IN PRODUCTION!")
        
        # Check database path exists
        if cls.DATABASE_URL.startswith("sqlite:///"):
            db_path = Path(cls.DATABASE_URL.replace("sqlite:///", ""))
            db_dir = db_path.parent
            if not db_dir.exists():
                try:
                    db_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created database directory: {db_dir}")
                except Exception as e:
                    validations.append(f"Cannot create database directory {db_dir}: {e}")
        
        # Check EPG cache directory exists
        epg_cache_path = Path(cls.EPG_CACHE_FILE)
        epg_cache_dir = epg_cache_path.parent
        if not epg_cache_dir.exists():
            try:
                epg_cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created EPG cache directory: {epg_cache_dir}")
            except Exception as e:
                validations.append(f"Cannot create EPG cache directory {epg_cache_dir}: {e}")
        
        # Port conflict check
        if cls.SERVER_PORT == cls.ACESTREAM_ENGINE_PORT:
            validations.append("SERVER_PORT and ACESTREAM_ENGINE_PORT cannot be the same")
        
        if cls.SERVER_PORT == cls.ACESTREAM_STREAMING_PORT:
            validations.append("SERVER_PORT and ACESTREAM_STREAMING_PORT cannot be the same")
        
        if cls.ACESTREAM_ENGINE_PORT == cls.ACESTREAM_STREAMING_PORT:
            validations.append("ACESTREAM_ENGINE_PORT and ACESTREAM_STREAMING_PORT cannot be the same")
        
        # URL validation for scraper and EPG
        for url in cls.SCRAPER_URLS:
            if not url.startswith(('http://', 'https://')):
                validations.append(f"Invalid SCRAPER_URL: {url} (must start with http:// or https://)")
        
        for url in cls.EPG_SOURCES:
            if not url.startswith(('http://', 'https://')):
                validations.append(f"Invalid EPG_SOURCE: {url} (must start with http:// or https://)")
        
        # Report validation issues
        if validations:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {v}" for v in validations)
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        logger.info("Configuration validation passed successfully")
        return True
    
    @classmethod
    def print_config(cls, hide_secrets: bool = True) -> None:
        """
        Print current configuration (for debugging)
        
        Args:
            hide_secrets: Whether to hide sensitive values
        """
        logger.info("=== Current Configuration ===")
        
        secret_fields = {'SECRET_KEY', 'ADMIN_PASSWORD'}
        
        for attr in dir(cls):
            if attr.isupper() and not attr.startswith('_'):
                value = getattr(cls, attr)
                if hide_secrets and attr in secret_fields:
                    value = "***HIDDEN***"
                logger.info(f"{attr}: {value}")

# Load and validate configuration at module import
Config.load()
Config.validate()
logger.info("Application configuration loaded successfully")


class ConfigAccessor:
    """Accessor class that provides lowercase attribute access to Config"""
    
    def __getattr__(self, name):
        # Try lowercase first
        upper_name = name.upper()
        if hasattr(Config, upper_name):
            return getattr(Config, upper_name)
        # Try as-is
        if hasattr(Config, name):
            return getattr(Config, name)
        raise AttributeError(f"Config has no attribute '{name}'")
    
    def get_scraper_urls_list(self) -> List[str]:
        """Get scraper URLs list"""
        return Config.SCRAPER_URLS
    
    def get_epg_sources_list(self) -> List[str]:
        """Get EPG sources list"""
        return Config.EPG_SOURCES


# Global config instance for easy access
_config_instance = None


def get_config() -> ConfigAccessor:
    """Get singleton configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigAccessor()
    return _config_instance


# Backward compatibility attributes
def __getattr__(name):
    """Allow module-level access to config attributes"""
    if hasattr(Config, name):
        return getattr(Config, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
