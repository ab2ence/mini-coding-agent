"""
Tests for config loader precedence rules.

Tests verify the fallback order: env var > local config > default config
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from config import ConfigLoader, load_config, ConfigError


class TestConfigLoaderDefaults:
    """Test default configuration values."""

    def test_default_database_config(self):
        """Test default database configuration."""
        loader = ConfigLoader()
        config = loader.load()

        assert config['database']['host'] == 'localhost'
        assert config['database']['port'] == 5432
        assert config['database']['name'] == 'myapp'
        assert config['database']['pool_size'] == 5

    def test_default_cache_config(self):
        """Test default cache configuration."""
        loader = ConfigLoader()
        config = loader.load()

        assert config['cache']['enabled'] is True
        assert config['cache']['ttl'] == 300
        assert config['cache']['max_size'] == 1000

    def test_default_logging_config(self):
        """Test default logging configuration."""
        loader = ConfigLoader()
        config = loader.load()

        assert config['logging']['level'] == 'INFO'
        assert '%(levelname)s' in config['logging']['format']

    def test_default_features_config(self):
        """Test default features configuration."""
        loader = ConfigLoader()
        config = loader.load()

        assert config['features']['beta'] is False
        assert config['features']['analytics'] is True


class TestLocalConfigOverride:
    """Test local config file override."""

    def test_local_config_overrides_defaults(self, tmp_path):
        """Test that local config overrides default values."""
        # Create config.json
        config_file = tmp_path / 'config.json'
        config_data = {
            'database': {
                'host': 'local-db.example.com',
                'port': 5433
            }
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Load config
        loader = ConfigLoader(tmp_path)
        config = loader.load()

        # Check overridden values
        assert config['database']['host'] == 'local-db.example.com'
        assert config['database']['port'] == 5433

        # Check unchanged values from defaults
        assert config['database']['name'] == 'myapp'
        assert config['database']['pool_size'] == 5

    def test_local_config_partial_override(self, tmp_path):
        """Test that partial local config only overrides specified values."""
        # Create config.json with only cache settings
        config_file = tmp_path / 'config.json'
        config_data = {
            'cache': {
                'enabled': False,
                'ttl': 600
            }
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Load config
        loader = ConfigLoader(tmp_path)
        config = loader.load()

        # Check overridden cache values
        assert config['cache']['enabled'] is False
        assert config['cache']['ttl'] == 600

        # Check other sections still use defaults
        assert config['database']['host'] == 'localhost'

    def test_no_local_config(self, tmp_path):
        """Test loading with no local config file."""
        loader = ConfigLoader(tmp_path)
        config = loader.load()

        # Should return all defaults
        assert config == ConfigLoader.DEFAULT_CONFIG


class TestEnvVarOverride:
    """Test environment variable override."""

    def test_env_var_overrides_default(self, monkeypatch):
        """Test that env var overrides default values."""
        monkeypatch.setenv('APP_DATABASE_HOST', 'env-db.example.com')
        monkeypatch.setenv('APP_CACHE_ENABLED', 'false')

        loader = ConfigLoader()
        config = loader.load()

        # Check env var overrides
        assert config['database']['host'] == 'env-db.example.com'
        assert config['cache']['enabled'] is False

        # Check unchanged values from defaults
        assert config['database']['port'] == 5432
        assert config['cache']['ttl'] == 300

    def test_env_var_type_conversion(self, monkeypatch):
        """Test that env vars are properly type-converted."""
        monkeypatch.setenv('APP_DATABASE_PORT', '5434')
        monkeypatch.setenv('APP_CACHE_MAX_SIZE', '2000')

        loader = ConfigLoader()
        config = loader.load()

        # Check type conversion
        assert isinstance(config['database']['port'], int)
        assert config['database']['port'] == 5434

        assert isinstance(config['cache']['max_size'], int)
        assert config['cache']['max_size'] == 2000

    def test_env_var_boolean_conversion(self, monkeypatch):
        """Test boolean env var conversion."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('yes', True),
            ('no', False),
            ('1', True),
            ('0', False),
            ('on', True),
            ('off', False),
        ]

        for value, expected in test_cases:
            monkeypatch.setenv('APP_FEATURES_BETA', value)
            loader = ConfigLoader()
            config = loader.load()
            assert config['features']['beta'] == expected, f"Failed for {value}"


class TestPrecedenceOrder:
    """Test the complete precedence order: env > local > default."""

    def test_env_var_has_highest_precedence(self, tmp_path, monkeypatch):
        """Test that env vars override both local and default."""
        # Create local config
        config_file = tmp_path / 'config.json'
        config_data = {
            'database': {
                'host': 'local-db.example.com',
                'port': 5433
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Set env var
        monkeypatch.setenv('APP_DATABASE_HOST', 'env-db.example.com')
        monkeypatch.setenv('APP_CACHE_ENABLED', 'false')

        # Load config
        loader = ConfigLoader(tmp_path)
        config = loader.load()

        # Env var should win
        assert config['database']['host'] == 'env-db.example.com'
        assert config['cache']['enabled'] is False

        # Local config should apply where env vars don't exist
        assert config['database']['port'] == 5433

        # Defaults should apply where neither env nor local exist
        assert config['database']['name'] == 'myapp'

    def test_local_config_overrides_default(self, tmp_path):
        """Test that local config overrides defaults."""
        # Create local config
        config_file = tmp_path / 'config.json'
        config_data = {
            'logging': {
                'level': 'DEBUG',
                'format': 'custom format'
            }
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        # Load config without env vars
        loader = ConfigLoader(tmp_path)
        config = loader.load()

        # Local config should override defaults
        assert config['logging']['level'] == 'DEBUG'
        assert config['logging']['format'] == 'custom format'

        # Other sections should still use defaults
        assert config['database']['host'] == 'localhost'


class TestConfigGet:
    """Test the get() method."""

    def test_get_section(self):
        """Test getting entire section."""
        loader = ConfigLoader()
        loader.load()

        db = loader.get('database')
        assert db['host'] == 'localhost'
        assert db['port'] == 5432

    def test_get_specific_key(self):
        """Test getting specific key."""
        loader = ConfigLoader()
        loader.load()

        host = loader.get('database', 'host')
        assert host == 'localhost'

    def test_get_with_default(self):
        """Test getting with default value."""
        loader = ConfigLoader()
        loader.load()

        value = loader.get('nonexistent', 'key', 'default_value')
        assert value == 'default_value'

    def test_get_nested_key_with_default(self):
        """Test getting nested key that doesn't exist."""
        loader = ConfigLoader()
        loader.load()

        value = loader.get('database', 'nonexistent', 'default')
        assert value == 'default'
