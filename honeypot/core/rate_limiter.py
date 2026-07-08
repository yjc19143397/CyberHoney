import time
import threading
import subprocess
import os

class RateLimiter:
    def __init__(self, config):
        self.config = config
        self.ip_data = {}
        self.blocked_ips = {}
        self.lock = threading.Lock()
        self._load_config()
        self._start_cleanup_thread()
    
    def _load_config(self):
        self.max_connections = self.config.get('rate_limiting.max_connections', 10)
        self.max_credentials = self.config.get('rate_limiting.max_credentials', 5)
        self.time_window = self.config.get('rate_limiting.time_window', 60)
        self.block_duration = self.config.get('rate_limiting.block_duration', 300)
        self.enable_response_delay = self.config.get('rate_limiting.response_delay.enable', True)
        self.base_delay = self.config.get('rate_limiting.response_delay.base_ms', 1000)
        self.max_delay = self.config.get('rate_limiting.response_delay.max_ms', 10000)
        self.enable_tarpit = self.config.get('rate_limiting.tarpit.enable', True)
        self.tarpit_threshold = self.config.get('rate_limiting.tarpit.threshold', 10)
    
    def _start_cleanup_thread(self):
        def cleanup():
            while True:
                now = time.time()
                with self.lock:
                    expired = [ip for ip, data in self.ip_data.items() 
                              if now - data['last_seen'] > self.time_window]
                    for ip in expired:
                        del self.ip_data[ip]
                    
                    expired_blocks = [ip for ip, timestamp in self.blocked_ips.items() 
                                     if now - timestamp > self.block_duration]
                    for ip in expired_blocks:
                        del self.blocked_ips[ip]
                
                time.sleep(60)
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def is_blocked(self, ip):
        with self.lock:
            if ip in self.blocked_ips:
                if time.time() - self.blocked_ips[ip] > self.block_duration:
                    del self.blocked_ips[ip]
                    return False
                return True
        return False
    
    def block_ip(self, ip, reason="rate_limit"):
        with self.lock:
            self.blocked_ips[ip] = time.time()
        return True
    
    def record_connection(self, ip):
        with self.lock:
            if ip not in self.ip_data:
                self.ip_data[ip] = {
                    'connections': 0,
                    'credentials': 0,
                    'requests': 0,
                    'last_seen': time.time(),
                    'first_seen': time.time()
                }
            
            self.ip_data[ip]['connections'] += 1
            self.ip_data[ip]['last_seen'] = time.time()
            
            count = self.ip_data[ip]['connections']
            if count >= self.max_connections:
                self.block_ip(ip, "connection_limit")
                return False
        
        return True
    
    def record_credential_attempt(self, ip):
        with self.lock:
            if ip not in self.ip_data:
                self.ip_data[ip] = {
                    'connections': 0,
                    'credentials': 0,
                    'requests': 0,
                    'last_seen': time.time(),
                    'first_seen': time.time()
                }
            
            self.ip_data[ip]['credentials'] += 1
            self.ip_data[ip]['last_seen'] = time.time()
            
            count = self.ip_data[ip]['credentials']
            if count >= self.max_credentials:
                self.block_ip(ip, "credential_limit")
                return False
        
        return True
    
    def record_request(self, ip):
        with self.lock:
            if ip not in self.ip_data:
                self.ip_data[ip] = {
                    'connections': 0,
                    'credentials': 0,
                    'requests': 0,
                    'last_seen': time.time(),
                    'first_seen': time.time()
                }
            
            self.ip_data[ip]['requests'] += 1
            self.ip_data[ip]['last_seen'] = time.time()
        
        return True
    
    def get_delay(self, ip):
        if not self.enable_response_delay:
            return 0
        
        with self.lock:
            if ip not in self.ip_data:
                return 0
            
            attempts = self.ip_data[ip]['credentials'] + self.ip_data[ip]['connections']
            delay = self.base_delay * (1 + attempts * 0.5)
            return min(delay, self.max_delay) / 1000.0
    
    def should_tarpit(self, ip):
        if not self.enable_tarpit:
            return False
        
        with self.lock:
            if ip not in self.ip_data:
                return False
            
            total_attempts = self.ip_data[ip]['credentials'] + self.ip_data[ip]['connections']
            return total_attempts >= self.tarpit_threshold
    
    def get_status(self, ip):
        with self.lock:
            if ip in self.blocked_ips:
                return {'blocked': True}
            if ip in self.ip_data:
                return {
                    'blocked': False,
                    'connections': self.ip_data[ip]['connections'],
                    'credentials': self.ip_data[ip]['credentials'],
                    'requests': self.ip_data[ip]['requests'],
                    'last_seen': self.ip_data[ip]['last_seen']
                }
            return {'blocked': False}
    
    def get_blocked_ips(self):
        with self.lock:
            return [(ip, time.time() - timestamp) for ip, timestamp in self.blocked_ips.items()]