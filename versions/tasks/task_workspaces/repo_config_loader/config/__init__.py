"""
Config Loader Module

Handles configuration loading with fallback precedence:
env var > local config > default config
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Base exception for config errors."""
    pass


class ConfigLoader:
    """
    Configuration loader with fallback support.

    Precedence order:
    1. Environment variables (highest priority)
    2. Local config file (config.json in current directory)
    3. Default config values (lowest priority)
    """

    DEFAULT_CONFIG = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'name': 'myapp',
            'pool_size': 5
        },
        'cache': {
            'enabled': True,
            'ttl': 300,
            'max_size': 1000
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'features': {
            'beta': False,
            'analytics': True
        }
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_dir: Directory containing config.json. Defaults to current dir.
        """
        self.config_dir = config_dir or Path.cwd()
        self._config = None

    def load(self) -> Dict[str, Any]:
        """
        Load configuration with fallback precedence.

        Returns:
            Merged configuration dictionary
        """
        # Start with default config
        config = self._deep_copy(self.DEFAULT_CONFIG)

        # Load and merge local config
        local_config = self._load_local_config()
        if local_config:
            config = self._merge_config(config, local_config)

        # Load and merge environment variables
        env_config = self._load_env_config()
        if env_config:
            config = self._merge_config(config, env_config)

        self._config = config
        return config

    def _load_local_config(self) -> Dict[str, Any]:
        """
        Load configuration from local config.json file.

        Returns:
            Local configuration or empty dict if not found
        """
        config_file = self.config_dir / 'config.json'

        if not config_file.exists():
            return {}

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigError(f"Failed to load config.json: {e}")

    def _load_env_config(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Environment variables follow the pattern:
        APP_SECTION_KEY=value

        Example:
            APP_DATABASE_HOST=db.example.com
            APP_CACHE_ENABLED=false

        Returns:
            Configuration dictionary from environment
        """
        config = {}
        prefix = 'APP_'

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Parse APP_SECTION_KEY
            parts = key[len(prefix):].lower().split('_', 1)

            if len(parts) < 2:
                continue

            section = parts[0]
            config_key = parts[1]

            # Initialize section if not exists
            if section not in config:
                config[section] = {}

            # Parse value (try to convert to appropriate type)
            parsed_value = self._parse_env_value(value)

            config[section][config_key] = parsed_value

        return config

    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type.

        Args:
            value: String value from environment

        Returns:
            Parsed value (bool, int, float, or string)
        """
        # Boolean
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False

        # Integer
        try:
            return int(value)
        except ValueError:
            pass

        # Float
        try:
            return float(value)
        except ValueError:
            pass

        # String
        return value

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge override config into base config.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = self._deep_copy(base)

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value

        return result

    def _deep_copy(self, obj: Any) -> Any:
        """Create deep copy of object."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            section: Config section name
            key: Optional key within section
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            self.load()

        if key is None:
            return self._config.get(section, default)

        return self._config.get(section, {}).get(key, default)


def load_config(config_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration.

    Args:
        config_dir: Optional config directory

    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader(config_dir)
    return loader.load()


__all__ = ['ConfigLoader', 'load_config', 'ConfigError']
