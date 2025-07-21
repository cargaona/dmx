"""Configuration management for dmx."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for dmx."""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".config" / "dmx"
        
        self.config_file = self.config_dir / "config.json"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                default_config = self._get_default_config()
                default_config.update(config)
                return default_config
        except (json.JSONDecodeError, OSError):
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "arl": "",
            "quality": "320",
            "output": str(Path.home() / "Downloads" / "Music"),
            "search_limit": 20,
            "download_dir": str(Path.home() / "Downloads" / "Music"),
            "debug": False,
            "cache_enabled": True,
            "cache_ttl": 3600,
            "rate_limit_per_second": 5.0,
            "max_concurrent_downloads": 3,
            "enable_real_apis": True,
            "log_level": "INFO",
        }
    
    def save(self):
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._config[key] = value
    
    @property
    def arl(self) -> str:
        """Get ARL token."""
        return self._config.get("arl", "")
    
    @arl.setter
    def arl(self, value: str):
        """Set ARL token."""
        self._config["arl"] = value
    
    @property
    def quality(self) -> str:
        """Get download quality."""
        return self._config.get("quality", "320")
    
    @quality.setter
    def quality(self, value: str):
        """Set download quality."""
        if value not in ["128", "320", "FLAC"]:
            raise ValueError(f"Invalid quality: {value}. Supported: 128, 320, FLAC")
        self._config["quality"] = value
    
    @property
    def output_dir(self) -> str:
        """Get output directory."""
        return self._config.get("output", str(Path.home() / "Downloads" / "Music"))
    
    @output_dir.setter
    def output_dir(self, value: str):
        """Set output directory."""
        self._config["output"] = value
    
    @property
    def search_limit(self) -> int:
        """Get search results limit."""
        return self._config.get("search_limit", 20)
    
    @search_limit.setter
    def search_limit(self, value: int):
        """Set search results limit."""
        self._config["search_limit"] = max(1, min(100, value))