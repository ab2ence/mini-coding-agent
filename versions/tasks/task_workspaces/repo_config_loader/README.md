# Config Loader

Configuration loader with fallback precedence support.

## Fallback Precedence

```
env var > local config > default config
```

## Installation

```bash
pip install -e .
```

## Usage

```python
from config import load_config

# Load with default precedence
config = load_config()

# Access values
db_host = config['database']['host']
```

## Environment Variables

Prefix with `APP_`:

```bash
export APP_DATABASE_HOST=db.example.com
export APP_CACHE_ENABLED=false
```

## Testing

```bash
pytest -v
```
