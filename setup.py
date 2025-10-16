#!/usr/bin/env python3
"""
Interactive Setup Wizard for Unified IPTV AceStream Platform
"""
import os
import sys
import secrets
from pathlib import Path


class Colors:
    """Terminal colors"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def load_env_example():
    """Load default values from .env.example"""
    defaults = {}
    env_example_path = Path(".env.example")
    
    if not env_example_path.exists():
        print_warning(".env.example not found, using hardcoded defaults")
        return defaults
    
    try:
        with open(env_example_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    defaults[key.strip()] = value.strip()
        
        print_info(f"Loaded {len(defaults)} default values from .env.example")
    except Exception as e:
        print_warning(f"Error reading .env.example: {e}")
    
    return defaults


def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_section(text):
    """Print section header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}» {text}{Colors.END}")
    print(f"{Colors.CYAN}{'─' * 60}{Colors.END}")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def ask_input(prompt, default=None, required=False):
    """Ask for user input"""
    if default:
        prompt_text = f"{Colors.BOLD}{prompt}{Colors.END} [{default}]: "
    else:
        prompt_text = f"{Colors.BOLD}{prompt}{Colors.END}: "
    
    while True:
        value = input(prompt_text).strip()
        
        if not value and default:
            return default
        
        if not value and required:
            print_error("This field is required!")
            continue
        
        if not value:
            return None
        
        return value


def ask_yes_no(prompt, default=True):
    """Ask yes/no question"""
    default_str = "Y/n" if default else "y/N"
    prompt_text = f"{Colors.BOLD}{prompt}{Colors.END} [{default_str}]: "
    
    while True:
        value = input(prompt_text).strip().lower()
        
        if not value:
            return default
        
        if value in ['y', 'yes', 'si', 'sì']:
            return True
        
        if value in ['n', 'no']:
            return False
        
        print_error("Please answer with y/yes or n/no")


def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(64)


def setup_server_config(defaults):
    """Setup server configuration"""
    print_section("Server Configuration")
    
    config = {}
    
    print_info("The server will listen on a single unified port")
    config['SERVER_HOST'] = ask_input("Server host", defaults.get('SERVER_HOST', '0.0.0.0'))
    
    port = ask_input("Server port", defaults.get('SERVER_PORT', '6880'))
    try:
        config['SERVER_PORT'] = str(int(port))
    except ValueError:
        default_port = defaults.get('SERVER_PORT', '6880')
        print_warning(f"Invalid port, using default {default_port}")
        config['SERVER_PORT'] = default_port
    
    config['SERVER_TIMEZONE'] = ask_input("Timezone", defaults.get('SERVER_TIMEZONE', 'Europe/Rome'))
    
    default_debug = defaults.get('SERVER_DEBUG', 'false').lower() == 'true'
    config['SERVER_DEBUG'] = "true" if ask_yes_no("Enable debug mode?", default_debug) else "false"
    
    return config


def setup_acestream_config(defaults):
    """Setup AceStream configuration"""
    print_section("AceStream Configuration")
    
    config = {}
    
    default_enabled = defaults.get('ACESTREAM_ENABLED', 'true').lower() == 'true'
    if not ask_yes_no("Enable AceStream engine?", default_enabled):
        config['ACESTREAM_ENABLED'] = "false"
        return config
    
    config['ACESTREAM_ENABLED'] = "true"
    config['ACESTREAM_ENGINE_HOST'] = ask_input("AceStream engine host", 
                                                 defaults.get('ACESTREAM_ENGINE_HOST', 'localhost'))
    
    port = ask_input("AceStream engine port", defaults.get('ACESTREAM_ENGINE_PORT', '6878'))
    try:
        config['ACESTREAM_ENGINE_PORT'] = str(int(port))
    except ValueError:
        config['ACESTREAM_ENGINE_PORT'] = defaults.get('ACESTREAM_ENGINE_PORT', '6878')
    
    timeout = ask_input("Stream timeout (seconds)", defaults.get('ACESTREAM_TIMEOUT', '15'))
    try:
        config['ACESTREAM_TIMEOUT'] = str(int(timeout))
    except ValueError:
        config['ACESTREAM_TIMEOUT'] = defaults.get('ACESTREAM_TIMEOUT', '15')
    
    print_info("\nAdvanced AceStream settings (press Enter to use defaults)")
    
    config['ACESTREAM_STREAMING_HOST'] = ask_input("Streaming host", 
                                                     defaults.get('ACESTREAM_STREAMING_HOST', '127.0.0.1'))
    config['ACESTREAM_STREAMING_PORT'] = ask_input("Streaming port", 
                                                     defaults.get('ACESTREAM_STREAMING_PORT', '6881'))
    config['ACESTREAM_CHUNK_SIZE'] = ask_input("Chunk size (bytes)", 
                                                defaults.get('ACESTREAM_CHUNK_SIZE', '8192'))
    config['ACESTREAM_EMPTY_TIMEOUT'] = ask_input("Empty timeout (seconds)", 
                                                   defaults.get('ACESTREAM_EMPTY_TIMEOUT', '60.0'))
    config['ACESTREAM_NO_RESPONSE_TIMEOUT'] = ask_input("No response timeout (seconds)", 
                                                         defaults.get('ACESTREAM_NO_RESPONSE_TIMEOUT', '10.0'))
    
    return config


def setup_scraper_config(defaults):
    """Setup scraper configuration"""
    print_section("Scraper Configuration")
    
    config = {}
    
    print_info("Enter M3U playlist URLs (comma-separated) or leave empty")
    print_info("Example: http://example.com/playlist.m3u,http://another.com/list.m3u")
    
    config['SCRAPER_URLS'] = ask_input("M3U playlist URLs", defaults.get('SCRAPER_URLS', ''))
    
    interval = ask_input("Update interval (seconds)", defaults.get('SCRAPER_UPDATE_INTERVAL', '3600'))
    try:
        config['SCRAPER_UPDATE_INTERVAL'] = str(int(interval))
    except ValueError:
        config['SCRAPER_UPDATE_INTERVAL'] = defaults.get('SCRAPER_UPDATE_INTERVAL', '3600')
    
    return config


def setup_epg_config(defaults):
    """Setup EPG configuration"""
    print_section("EPG Configuration")
    
    config = {}
    
    print_info("EPG sources (comma-separated URLs)")
    config['EPG_SOURCES'] = ask_input("EPG sources", defaults.get('EPG_SOURCES', ''))
    
    interval = ask_input("Update interval (seconds)", defaults.get('EPG_UPDATE_INTERVAL', '86400'))
    try:
        config['EPG_UPDATE_INTERVAL'] = str(int(interval))
    except ValueError:
        config['EPG_UPDATE_INTERVAL'] = defaults.get('EPG_UPDATE_INTERVAL', '86400')
    
    config['EPG_CACHE_FILE'] = ask_input("Cache file path", defaults.get('EPG_CACHE_FILE', 'data/epg.xml'))
    
    return config


def setup_database_config(defaults):
    """Setup database configuration"""
    print_section("Database Configuration")
    
    config = {}
    
    print_info("SQLite database will be used by default")
    config['DATABASE_URL'] = ask_input("Database URL", 
                                        defaults.get('DATABASE_URL', 'sqlite:///data/unified-iptv.db'))
    
    default_echo = defaults.get('DATABASE_ECHO', 'false').lower() == 'true'
    config['DATABASE_ECHO'] = "true" if ask_yes_no("Echo SQL queries?", default_echo) else "false"
    
    print_info("\nConnection pool settings")
    pool_size = ask_input("Pool size", defaults.get('DATABASE_POOL_SIZE', '10'))
    try:
        config['DATABASE_POOL_SIZE'] = str(int(pool_size))
    except ValueError:
        config['DATABASE_POOL_SIZE'] = defaults.get('DATABASE_POOL_SIZE', '10')
    
    max_overflow = ask_input("Max overflow", defaults.get('DATABASE_MAX_OVERFLOW', '20'))
    try:
        config['DATABASE_MAX_OVERFLOW'] = str(int(max_overflow))
    except ValueError:
        config['DATABASE_MAX_OVERFLOW'] = defaults.get('DATABASE_MAX_OVERFLOW', '20')
    
    return config


def setup_admin_config(defaults):
    """Setup admin configuration"""
    print_section("Admin User Configuration")
    
    config = {}
    
    print_warning("IMPORTANT: Change these credentials in production!")
    
    config['ADMIN_USERNAME'] = ask_input("Admin username", 
                                          defaults.get('ADMIN_USERNAME', 'admin'), 
                                          required=True)
    
    while True:
        password = ask_input("Admin password", 
                           defaults.get('ADMIN_PASSWORD', 'changeme'), 
                           required=True)
        if len(password) < 6:
            print_error("Password must be at least 6 characters long")
            continue
        
        if password == "changeme":
            if not ask_yes_no("Using default password is insecure. Continue anyway?", False):
                continue
        
        config['ADMIN_PASSWORD'] = password
        break
    
    return config


def setup_security_config(defaults):
    """Setup security configuration"""
    print_section("Security Configuration")
    
    config = {}
    
    # Always generate a new secret key for security
    print_info("Generating secure secret key...")
    config['SECRET_KEY'] = generate_secret_key()
    print_success(f"Generated secret key (64 bytes)")
    
    expire = ask_input("Access token expiry (minutes)", 
                      defaults.get('ACCESS_TOKEN_EXPIRE_MINUTES', '43200'))
    try:
        config['ACCESS_TOKEN_EXPIRE_MINUTES'] = str(int(expire))
    except ValueError:
        config['ACCESS_TOKEN_EXPIRE_MINUTES'] = defaults.get('ACCESS_TOKEN_EXPIRE_MINUTES', '43200')
    
    return config


def write_env_file(config, filepath=".env"):
    """Write configuration to .env file"""
    print_section("Writing Configuration")
    
    try:
        with open(filepath, 'w') as f:
            f.write("# Unified IPTV AceStream Platform Configuration\n")
            f.write("# Generated by setup wizard\n\n")
            
            # Server
            f.write("# Server Configuration\n")
            for key in ['SERVER_HOST', 'SERVER_PORT', 'SERVER_TIMEZONE', 'SERVER_DEBUG']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            
            # AceStream
            f.write("\n# AceStream Configuration\n")
            for key in ['ACESTREAM_ENABLED', 'ACESTREAM_ENGINE_HOST', 'ACESTREAM_ENGINE_PORT', 
                       'ACESTREAM_TIMEOUT']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            
            # AceStream Streaming
            f.write("\n# AceStream Streaming Server (internal)\n")
            for key in ['ACESTREAM_STREAMING_HOST', 'ACESTREAM_STREAMING_PORT', 
                       'ACESTREAM_CHUNK_SIZE', 'ACESTREAM_EMPTY_TIMEOUT', 
                       'ACESTREAM_NO_RESPONSE_TIMEOUT']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            
            # Scraper
            f.write("\n# Scraper Configuration\n")
            for key in ['SCRAPER_URLS', 'SCRAPER_UPDATE_INTERVAL']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            
            # EPG
            f.write("\n# EPG Configuration\n")
            for key in ['EPG_SOURCES', 'EPG_UPDATE_INTERVAL', 'EPG_CACHE_FILE']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            
            # Database
            f.write("\n# Database Configuration\n")
            for key in ['DATABASE_URL', 'DATABASE_ECHO', 'DATABASE_POOL_SIZE', 
                       'DATABASE_MAX_OVERFLOW']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            
            # Admin
            f.write("\n# Admin User\n")
            for key in ['ADMIN_USERNAME', 'ADMIN_PASSWORD']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
            
            # Security
            f.write("\n# Security\n")
            for key in ['SECRET_KEY', 'ACCESS_TOKEN_EXPIRE_MINUTES']:
                if key in config:
                    f.write(f"{key}={config[key]}\n")
        
        print_success(f"Configuration written to {filepath}")
        return True
        
    except Exception as e:
        print_error(f"Failed to write configuration: {e}")
        return False


def create_directories():
    """Create required directories"""
    print_section("Creating Directories")
    
    directories = ['data', 'data/epg', 'logs', 'config']
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created: {directory}")
        else:
            print_info(f"Already exists: {directory}")


def initialize_database():
    """Initialize database"""
    print_section("Initializing Database")
    
    try:
        from app.utils.auth import init_db
        init_db()
        print_success("Database initialized successfully")
        return True
    except Exception as e:
        print_error(f"Database initialization failed: {e}")
        return False


def main():
    """Main setup wizard"""
    print_header("Unified IPTV AceStream Setup Wizard")
    
    print_info("This wizard will guide you through the initial configuration")
    print()
    
    # Load defaults from .env.example
    defaults = load_env_example()
    print()
    
    # Check if .env already exists
    if Path(".env").exists():
        print_warning(".env file already exists!")
        if not ask_yes_no("Do you want to overwrite it?", False):
            print_info("Setup cancelled")
            return
        print()
    
    # Collect all configuration
    config = {}
    
    config.update(setup_server_config(defaults))
    config.update(setup_acestream_config(defaults))
    config.update(setup_scraper_config(defaults))
    config.update(setup_epg_config(defaults))
    config.update(setup_database_config(defaults))
    config.update(setup_admin_config(defaults))
    config.update(setup_security_config(defaults))
    
    # Create directories
    create_directories()
    
    # Write configuration
    if not write_env_file(config):
        print_error("\nSetup failed!")
        return 1
    
    # Initialize database
    if not initialize_database():
        print_warning("\nDatabase initialization failed, but you can try again later")
        print_info("Run: python setup.py")
    
    # Final message
    print_header("Setup Complete!")
    
    print_success("Configuration has been saved to .env")
    print()
    print_info("Next steps:")
    print(f"  1. Review your configuration: {Colors.BOLD}nano .env{Colors.END}")
    print(f"  2. Start the application: {Colors.BOLD}python main.py{Colors.END}")
    print(f"  3. Or use Docker: {Colors.BOLD}docker-compose up -d{Colors.END}")
    print()
    print_info("Dashboard Access:")
    print(f"  • URL: {Colors.BOLD}http://localhost:{config.get('SERVER_PORT', defaults.get('SERVER_PORT', '6880'))}{Colors.END}")
    print(f"  • Username: {Colors.BOLD}{config.get('ADMIN_USERNAME', 'admin')}{Colors.END}")
    print(f"  • Password: {Colors.BOLD}{config.get('ADMIN_PASSWORD', '***')}{Colors.END}")
    print()
    print_info("Xtream API:")
    print(f"  • URL: {Colors.BOLD}http://localhost:{config.get('SERVER_PORT', defaults.get('SERVER_PORT', '6880'))}/player_api.php{Colors.END}")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        sys.exit(1)
