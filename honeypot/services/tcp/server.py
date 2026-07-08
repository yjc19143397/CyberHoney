import socket
import threading
import time


class TCPServer:
    def __init__(self, config, logger, database, rate_limiter=None):
        self.config = config
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.host = config.get('honeypot.host', '0.0.0.0')
        self.port = config.get('services.tcp.port', 1234)
        self.banner = config.get('services.tcp.banner', 'Welcome to TCP Service')
        self.response = config.get('services.tcp.response', 'Received your message')
        self.running = False
        self.server_socket = None
    
    def handle_client(self, client_socket, client_addr):
        client_ip = client_addr[0]
        client_port = client_addr[1]
        
        if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
            self.logger.warning(f"Blocked TCP connection from {client_ip}:{client_port}")
            client_socket.close()
            return
        
        if self.rate_limiter and self.rate_limiter.should_tarpit(client_ip):
            self.logger.warning(f"Tarpitting TCP connection from {client_ip}:{client_port}")
            time.sleep(30)
            client_socket.close()
            return
        
        try:
            self.logger.info(f"TCP connection from {client_ip}:{client_port}")
            self.database.log_connection(client_ip, client_port, 'tcp', 'TCP', 'connected')
            
            if self.rate_limiter:
                if not self.rate_limiter.record_connection(client_ip):
                    self.logger.warning(f"IP {client_ip} blocked due to excessive connections")
            
            if self.banner:
                client_socket.sendall((self.banner + '\n').encode())
            
            buffer = b''
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    buffer += data
                    
                    self.logger.info(f"TCP data from {client_ip}:{client_port}: {data.decode(errors='replace')}")
                    
                    if self.response:
                        client_socket.sendall((self.response + '\n').encode())
                    
                except socket.timeout:
                    break
                except Exception as e:
                    self.logger.error(f"TCP handler error for {client_ip}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"TCP connection error for {client_ip}: {e}")
        finally:
            self.database.log_connection(client_ip, client_port, 'tcp', 'TCP', 'disconnected')
            client_socket.close()
    
    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1.0)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            self.logger.info(f"TCP honeypot listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    client_socket.settimeout(30)
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"TCP server error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start TCP server: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error stopping TCP server: {e}")
    
    def is_running(self):
        return self.running