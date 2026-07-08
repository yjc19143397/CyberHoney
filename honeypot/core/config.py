import yaml
import os

class Config:
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        default_config = {
            'honeypot': {
                'name': 'CyberHoney',
                'host': '0.0.0.0'
            },
            'services': {
                'ssh': {
                    'enabled': True,
                    'port': 2222,
                    'banner': 'SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5'
                },
                'ftp': {
                    'enabled': True,
                    'port': 2121,
                    'banner': '220 Welcome to FTP Server'
                },
                'http': {
                    'enabled': True,
                    'port': 8080,
                    'ssl_enabled': False,
                    'ssl_port': 8443
                }
            },
            'database': {
                'type': 'sqlite',
                'path': 'data/honeypot.db'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/honeypot.log',
                'max_size': 10485760,
                'backup_count': 5
            },
            'api': {
                'enabled': True,
                'port': 5000,
                'allowed_ips': ['127.0.0.1', '::1']
            },
            'rate_limiting': {
                'max_connections': 10,
                'max_credentials': 5,
                'time_window': 60,
                'block_duration': 300,
                'response_delay': {
                    'enable': True,
                    'base_ms': 1000,
                    'max_ms': 10000
                },
                'tarpit': {
                    'enable': True,
                    'threshold': 10
                }
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(default_config, user_config)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config
    
    def _merge_config(self, default, user):
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
            if value is None:
                return default
        return value