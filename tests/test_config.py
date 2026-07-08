import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from honeypot.core.config import Config

class TestConfig:
    def test_default_config(self):
        config = Config('/nonexistent/config.yaml')
        assert config.get('honeypot.name') == 'CyberHoney'
        assert config.get('honeypot.host') == '0.0.0.0'
    
    def test_config_loading(self):
        config = Config('config.yaml')
        assert config.get('honeypot.name') == 'CyberHoney'
        assert config.get('services.ssh.enabled') == True
    
    def test_config_get_nested(self):
        config = Config('config.yaml')
        assert config.get('services.ssh.port') == 2222
        assert config.get('services.ftp.port') == 2121
    
    def test_config_get_default(self):
        config = Config('config.yaml')
        assert config.get('nonexistent.key', 'default') == 'default'