import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from honeypot.core.config import Config
from honeypot.core.database import Database

class TestDatabase:
    def setup_method(self):
        config = Config('config.yaml')
        self.db = Database(config)
    
    def teardown_method(self):
        self.db.close()
    
    def test_log_connection(self):
        self.db.log_connection('192.168.1.1', 12345, 'ssh', 'TCP', 'connected', 'test')
        logs = self.db.get_connection_logs(1)
        assert len(logs) == 1
        assert logs[0].source_ip == '192.168.1.1'
        assert logs[0].service == 'ssh'
    
    def test_log_credential_attempt(self):
        self.db.log_credential_attempt('192.168.1.1', 'ssh', 'admin', 'password', False)
        attempts = self.db.get_credential_attempts(1)
        assert len(attempts) == 1
        assert attempts[0].username == 'admin'
        assert attempts[0].password == 'password'
    
    def test_log_http_request(self):
        self.db.log_http_request('192.168.1.1', 'GET', '/test', {'Host': 'localhost'}, 'body', 'test-agent', 200)
        requests = self.db.get_http_requests(1)
        assert len(requests) == 1
        assert requests[0].method == 'GET'
        assert requests[0].path == '/test'