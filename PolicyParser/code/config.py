"""
Configuration file for Privacy Policy Parser
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class WebDriverConfig:
    """WebDriver configuration"""
    firefox_binary_path: str = "/bigtemp/fr3ya/cosmic/webdriver/firefox/firefox"
    geckodriver_path: str = "/u/fr3ya/miniforge3/bin/geckodriver"
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    wait_time: int = 30  # seconds to wait for page load

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    enabled: bool = True
    http_proxy: str = "http://127.0.0.1:3128"
    https_proxy: str = "http://127.0.0.1:3128"
    
    @property
    def proxies(self) -> Optional[Dict[str, str]]:
        if self.enabled:
            return {
                'http': self.http_proxy,
                'https': self.https_proxy,
            }
        return None

@dataclass
class ParserConfig:
    """Parser configuration"""
    timeout: int = 20  # HTTP request timeout
    max_tokens: int = 6  # Maximum tokens for privacy link text
    popup_max_tokens: int = 4  # Maximum tokens for popup privacy link text
    enable_translation: bool = False  # Enable translation for non-English sites
    retry_attempts: int = 2  # Number of retry attempts

@dataclass
class OutputConfig:
    """Output configuration"""
    output_dir: str = "../data/new_pp"
    links_file: str = "privacy_policy_links.json"
    enable_screenshots: bool = True
    save_raw_html: bool = False

@dataclass
class PrivacyPolicyConfig:
    """Main configuration class"""
    webdriver: WebDriverConfig = field(default_factory=WebDriverConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'PrivacyPolicyConfig':
        """Load configuration from JSON file"""
        import json
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def to_file(self, config_path: str) -> None:
        """Save configuration to JSON file"""
        import json
        config_dict = {
            'webdriver': self.webdriver.__dict__,
            'proxy': self.proxy.__dict__,
            'parser': self.parser.__dict__,
            'output': self.output.__dict__
        }
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

# Default configuration
DEFAULT_CONFIG = PrivacyPolicyConfig()