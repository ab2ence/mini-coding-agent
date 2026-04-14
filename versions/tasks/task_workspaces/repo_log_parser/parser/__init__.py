"""
Log Parser - Core Module

A simple log parser that handles JSON, XML, and YAML formats.
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional


class LogParserError(Exception):
    """Base exception for log parser errors."""
    pass


class ParseError(LogParserError):
    """Exception raised when parsing fails."""
    pass


def parse_json(data: str) -> List[Dict[str, Any]]:
    """
    Parse JSON log entries from string.

    Args:
        data: JSON string containing log entries

    Returns:
        List of parsed log entries

    Raises:
        ParseError: If JSON parsing fails
    """
    try:
        parsed = json.loads(data)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return [parsed]
        else:
            raise ParseError(f"Unexpected JSON type: {type(parsed)}")
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e}")


def parse_xml(data: str) -> List[Dict[str, Any]]:
    """
    Parse XML log entries from string.

    Args:
        data: XML string containing log entries

    Returns:
        List of parsed log entries as dictionaries

    Raises:
        ParseError: If XML parsing fails
    """
    try:
        root = ET.fromstring(data)
        entries = []

        for entry in root.findall('.//entry'):
            entry_dict = {}
            for child in entry:
                entry_dict[child.tag] = child.text or child.get('value', '')

            # Handle attributes
            for attr, value in entry.attrib.items():
                entry_dict[f"@{attr}"] = value

            entries.append(entry_dict)

        return entries

    except ET.ParseError as e:
        raise ParseError(f"Invalid XML: {e}")


def parse_log_entry(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single log line.

    Args:
        line: A single log line

    Returns:
        Parsed log entry or None if parsing fails
    """
    line = line.strip()
    if not line:
        return None

    # Try JSON first
    if line.startswith('{') or line.startswith('['):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            pass

    # Parse key=value format
    if '=' in line:
        parts = line.split()
        result = {}
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                result[key] = value
        if result:
            return result

    return {'raw': line}


def validate_log_entry(entry: Dict[str, Any]) -> bool:
    """
    Validate a log entry has required fields.

    Args:
        entry: Log entry dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ['timestamp', 'level', 'message']

    for field in required_fields:
        if field not in entry:
            return False

    return True


def parse_logs(data: str, format: str = 'auto') -> List[Dict[str, Any]]:
    """
    Parse logs in the specified or auto-detected format.

    Args:
        data: Log data string
        format: Format type ('json', 'xml', 'keyvalue', 'auto')

    Returns:
        List of parsed log entries

    Raises:
        ParseError: If parsing fails
    """
    if format == 'json':
        return parse_json(data)
    elif format == 'xml':
        return parse_xml(data)
    elif format == 'keyvalue':
        lines = data.strip().split('\n')
        results = []
        for line in lines:
            parsed = parse_log_entry(line)
            if parsed:
                results.append(parsed)
        return results
    else:
        # Auto-detect format
        data = data.strip()

        if data.startswith('{') or data.startswith('['):
            try:
                return parse_json(data)
            except ParseError:
                pass

        if data.startswith('<'):
            try:
                return parse_xml(data)
            except ParseError:
                pass

        # Default to key-value parsing
        return parse_logs(data, 'keyvalue')


__all__ = [
    'parse_json', 'parse_xml', 'parse_log_entry',
    'parse_logs', 'validate_log_entry',
    'LogParserError', 'ParseError'
]
