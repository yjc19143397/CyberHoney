import socket
import threading
import time


class TelnetServer:
    def __init__(self, config, logger, database, rate_limiter=None):
        self.config = config
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.host = config.get('honeypot.host', '0.0.0.0')
        self.port = config.get('services.telnet.port', 2323)
        self.banner = config.get('services.telnet.banner', 'Welcome to Telnet Server')
        self.prompt = config.get('services.telnet.prompt', '> ')
        self.running = False
        self.server_socket = None
    
    def _send(self, conn, data):
        if isinstance(data, str):
            data = data.encode()
        conn.sendall(data)
    
    def _recv(self, conn, bufsize=1024):
        return conn.recv(bufsize)
    
    def handle_client(self, client_socket, client_addr):
        client_ip = client_addr[0]
        client_port = client_addr[1]
        
        if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
            self.logger.warning(f"Blocked Telnet connection from {client_ip}:{client_port}")
            client_socket.close()
            return
        
        if self.rate_limiter and self.rate_limiter.should_tarpit(client_ip):
            self.logger.warning(f"Tarpitting Telnet connection from {client_ip}:{client_port}")
            time.sleep(30)
            client_socket.close()
            return
        
        try:
            self.logger.info(f"Telnet connection from {client_ip}:{client_port}")
            self.database.log_connection(client_ip, client_port, 'telnet', 'TCP', 'connected')
            
            if self.rate_limiter:
                if not self.rate_limiter.record_connection(client_ip):
                    self.logger.warning(f"IP {client_ip} blocked due to excessive connections")
            
            if self.banner:
                self._send(client_socket, self.banner + '\r\n')
            
            authenticated = False
            username = None
            
            self._send(client_socket, 'Username: ')
            username_buf = b''
            
            while self.running:
                try:
                    data = client_socket.recv(1)
                    if not data:
                        break
                    
                    if data == b'\r' or data == b'\n':
                        username = username_buf.decode(errors='replace').strip()
                        self._send(client_socket, '\r\nPassword: ')
                        
                        password_buf = b''
                        while self.running:
                            pwd_data = client_socket.recv(1)
                            if not pwd_data:
                                break
                            
                            if pwd_data == b'\r' or pwd_data == b'\n':
                                password = password_buf.decode(errors='replace').strip()
                                
                                if self.rate_limiter:
                                    delay = self.rate_limiter.get_delay(client_ip)
                                    if delay > 0:
                                        time.sleep(delay)
                                
                                self.logger.warning(f"Telnet authentication attempt from {client_ip}: {username}/{password}")
                                self.database.log_credential_attempt(client_ip, 'telnet', username, password, False)
                                
                                if self.rate_limiter:
                                    if not self.rate_limiter.record_credential_attempt(client_ip):
                                        self.logger.warning(f"IP {client_ip} blocked due to excessive credential attempts")
                                        self._send(client_socket, '\r\nToo many attempts. Connection closed.\r\n')
                                        return
                                
                                authenticated = True
                                self._send(client_socket, '\r\nLogin successful\r\n')
                                break
                            elif pwd_data == b'\x08':
                                password_buf = password_buf[:-1]
                            else:
                                password_buf += pwd_data
                        
                        break
                    elif data == b'\x08':
                        username_buf = username_buf[:-1]
                    else:
                        username_buf += data
                
                except socket.timeout:
                    break
                except Exception as e:
                    self.logger.error(f"Telnet auth error for {client_ip}: {e}")
                    break
            
            if authenticated:
                self._send(client_socket, self.prompt)
                command_buf = b''
                
                while self.running:
                    try:
                        data = client_socket.recv(1)
                        if not data:
                            break
                        
                        if data == b'\r' or data == b'\n':
                            command = command_buf.decode(errors='replace').strip()
                            self._send(client_socket, '\r\n')
                            
                            if command.lower() == 'exit' or command.lower() == 'quit':
                                self._send(client_socket, 'Goodbye.\r\n')
                                break
                            elif command.lower() == 'help':
                                self._send(client_socket, 'Available commands: help, exit, quit, whoami, date, ls\r\n')
                            elif command.lower() == 'whoami':
                                self._send(client_socket, f'{username}\r\n')
                            elif command.lower() == 'date':
                                self._send(client_socket, time.strftime('%Y-%m-%d %H:%M:%S') + '\r\n')
                            elif command.lower() == 'ls':
                                self._send(client_socket, 'README.txt  config.ini  logs/\r\n')
                            elif command:
                                self.logger.warning(f"Telnet command from {client_ip}: {command}")
                                self._send(client_socket, f'Command not found: {command}\r\n')
                            
                            command_buf = b''
                            self._send(client_socket, self.prompt)
                        elif data == b'\x08':
                            command_buf = command_buf[:-1]
                        else:
                            command_buf += data
                    
                    except socket.timeout:
                        break
                    except Exception as e:
                        self.logger.error(f"Telnet command error for {client_ip}: {e}")
                        break
                    
        except Exception as e:
            self.logger.error(f"Telnet connection error for {client_ip}: {e}")
        finally:
            self.database.log_connection(client_ip, client_port, 'telnet', 'TCP', 'disconnected')
            client_socket.close()
    
    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.settimeout(1.0)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            self.logger.info(f"Telnet honeypot listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    client_socket.settimeout(60)
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Telnet server error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start Telnet server: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error stopping Telnet server: {e}")
    
    def is_running(self):
        return self.running