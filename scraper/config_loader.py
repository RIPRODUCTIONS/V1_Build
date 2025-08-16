import os
from pathlib import Path
from typing import Any

import yaml


def load_config(config_file: str = 'config.yaml') -> dict[str, Any]:
    """
    Loads config from YAML file and overrides with environment variables.
    Sensitive info like DB_CONN_STRING comes from env only.
    """
    config = {}

    # Try to load from config file
    config_path = Path(config_file)
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")

    # Override with environment variables
    env_overrides = {
        'db_conn_string': 'DB_CONN_STRING',
        'airflow_url': 'AIRFLOW_URL',
        'airflow_auth': 'AIRFLOW_AUTH',
        'max_concurrent': 'MAX_CONCURRENT',
        'timeout': 'TIMEOUT',
        'user_agent': 'USER_AGENT',
        'log_level': 'LOG_LEVEL',
        'output_dir': 'OUTPUT_DIR'
    }

    for config_key, env_var in env_overrides.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            # Convert string values to appropriate types
            if config_key in ['max_concurrent', 'timeout']:
                try:
                    config[config_key] = int(env_value)
                except ValueError:
                    print(f"Warning: Invalid {config_key} value: {env_value}")
            else:
                config[config_key] = env_value

    # Set defaults for missing values
    defaults = {
        'max_concurrent': 5,
        'timeout': 30000,
        'log_level': 'INFO',
        'output_dir': './output',
        'wait_for_network_idle': True,
        'retry_attempts': 3,
        'retry_delay': 5
    }

    for key, default_value in defaults.items():
        if key not in config:
            config[key] = default_value

    return config

def get_database_config() -> dict[str, str]:
    """Extract database configuration from environment or config"""
    config = load_config()

    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'scraper_db'),
        'username': os.getenv('DB_USER', 'scraper_user'),
        'password': os.getenv('DB_PASSWORD', ''),
        'conn_string': config.get('db_conn_string', '')
    }

    return db_config

def get_airflow_config() -> dict[str, str]:
    """Extract Airflow configuration from environment or config"""
    config = load_config()

    airflow_config = {
        'url': config.get('airflow_url', 'http://localhost:8080'),
        'auth': config.get('airflow_auth', ''),
        'dag_id': config.get('dag_id', 'automated_web_scraper'),
        'api_version': config.get('api_version', 'v1')
    }

    return airflow_config

def save_config(config: dict[str, Any], config_file: str = 'config.yaml') -> None:
    """Save configuration to YAML file"""
    try:
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print(f"Configuration saved to {config_file}")
    except Exception as e:
        print(f"Error saving configuration: {e}")

def create_default_config(config_file: str = 'config.yaml') -> None:
    """Create a default configuration file"""
    default_config = {
        'scraping': {
            'max_concurrent': 5,
            'timeout': 30000,
            'wait_for_network_idle': True,
            'retry_attempts': 3,
            'retry_delay': 5
        },
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'scraper_db',
            'username': 'scraper_user'
        },
        'airflow': {
            'url': 'http://localhost:8080',
            'dag_id': 'automated_web_scraper',
            'api_version': 'v1'
        },
        'logging': {
            'level': 'INFO',
            'output_dir': './output'
        }
    }

    save_config(default_config, config_file)
