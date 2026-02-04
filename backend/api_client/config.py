"""
Configuration management for XSIAM credentials
Stores API credentials securely (in production, use environment variables or secret management)
"""
import json
from pathlib import Path
from typing import Optional, Dict

CONFIG_FILE = Path(__file__).parent / "xsiam_config.json"


def save_config(fqdn: str, api_key: str, api_key_id: str) -> None:
    """Save XSIAM API configuration"""
    config = {
        "fqdn": fqdn,
        "api_key": api_key,
        "api_key_id": api_key_id
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def load_config() -> Optional[Dict]:
    """Load XSIAM API configuration"""
    if not CONFIG_FILE.exists():
        return None
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def clear_config() -> None:
    """Clear stored configuration"""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def is_configured() -> bool:
    """Check if XSIAM API is configured"""
    config = load_config()
    return config is not None and all(k in config for k in ['fqdn', 'api_key', 'api_key_id'])
