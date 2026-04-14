# Log Parser

A simple log parser supporting JSON, XML, and key-value formats.

## Installation

```bash
pip install -e .
```

## Usage

```python
from parser import parse_logs

# Parse JSON logs
logs = parse_logs('[{"timestamp": "2024-01-01", "level": "INFO"}]')

# Parse XML logs
logs = parse_logs('<logs><entry>Test</entry></logs>', format='xml')
```

## Testing

```bash
pytest -v
```
