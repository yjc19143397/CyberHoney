import socket
import threading
import time


class UDPServer:
    def __init__(self, config, logger, database, rate_limiter=None):
        self.config = config
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.host = config.get('honeypot.host', '0.0.0.0')
        self.port = config.get('services.udp.port', 5678)
        self.response = config.get('services.udp.response', 'Received')
        self.running = False
        self.server_socket = None
    
    def handle_client(self, data, client_addr):
        client_ip = client_addr[0]
        client_port = client_addr[1]
        
        if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
            self.logger.warning(f"Blocked UDP packet from {client_ip}:{client_port}")
            return
        
        try:
            self.logger.info(f"UDP packet from {client_ip}:{client_port}: {data.decode(errors='replace')}")
            self.database.log_connection(client_ip, client_port, 'udp', 'UDP', 'connected')
            
            if self.rate_limiter:
                if not self.rate_limiter.record_connection(client_ip):
                    self.logger.warning(f"IP {client_ip} blocked due to excessive connections")
            
            if self.response:
                self.server_socket.sendto((self.response + '\n').encode(), client_addr)
                
        except Exception as e:
            self.logger.error(f"UDP handler error for {client_ip}: {e}")
    
    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1.0)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.logger.info(f"UDP honeypot listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    data, client_addr = self.server_socket.recvfrom(1024)
                    thread = threading.Thread(target=self.handle_client, args=(data, client_addr), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"UDP server error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start UDP server: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error stopping UDP server: {e}")
    
    def is_running(self):
        return self.running