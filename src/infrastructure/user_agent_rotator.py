"""
User Agent Rotation Service

Provides random user agent strings for bot protection.
"""

import random
from typing import List

from ..domain.interfaces import IUserAgentRotator


class UserAgentRotator(IUserAgentRotator):
    """
    Service for rotating user agent strings to avoid detection.
    
    Features:
    - Random desktop user agents
    - Mobile user agents
    - Recent browser versions
    """
    
    def __init__(self, config):
        """
        Initialize with configuration.
        
        Args:
            config: Bot protection configuration
        """
        self.config = config
        self.desktop_agents = config.user_agent_list if hasattr(config, 'user_agent_list') else [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
        self.mobile_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        ]
    
    def get_random_user_agent(self) -> str:
        """Get a random desktop user agent string."""
        return random.choice(self.desktop_agents)
    
    def get_mobile_user_agent(self) -> str:
        """Get a random mobile user agent string."""
        return random.choice(self.mobile_agents) 