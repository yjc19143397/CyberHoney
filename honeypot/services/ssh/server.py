import socket
import threading
import paramiko
import os
import time

class SSHHoneypotHandler(paramiko.ServerInterface):
    def __init__(self, client_ip, logger, database, rate_limiter):
        self.client_ip = client_ip
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.authenticated = False
    
    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED
    
    def check_auth_password(self, username, password):
        if self.rate_limiter.is_blocked(self.client_ip):
            return paramiko.AUTH_FAILED
        
        delay = self.rate_limiter.get_delay(self.client_ip)
        if delay > 0:
            time.sleep(delay)
        
        self.logger.warning(f"SSH authentication attempt from {self.client_ip}: {username}/{password}")
        self.database.log_credential_attempt(self.client_ip, 'ssh', username, password, False)
        
        if not self.rate_limiter.record_credential_attempt(self.client_ip):
            self.logger.warning(f"IP {self.client_ip} blocked due to excessive credential attempts")
            return paramiko.AUTH_FAILED
        
        return paramiko.AUTH_FAILED
    
    def check_auth_publickey(self, username, key):
        if self.rate_limiter.is_blocked(self.client_ip):
            return paramiko.AUTH_FAILED
        
        self.logger.warning(f"SSH public key attempt from {self.client_ip}: {username}")
        return paramiko.AUTH_FAILED
    
    def check_channel_exec_request(self, channel, command):
        if self.authenticated:
            channel.send(f"Command executed: {command.decode()}\n")
            channel.send_exit_status(0)
        return True
    
    def get_allowed_auths(self, username):
        return 'password,publickey'

class SSHServer:
    def __init__(self, config, logger, database, rate_limiter=None):
        self.config = config
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.host = config.get('honeypot.host', '0.0.0.0')
        self.port = config.get('services.ssh.port', 2222)
        self.banner = config.get('services.ssh.banner', 'SSH-2.0-OpenSSH_8.2p1')
        self.running = False
        self.server_socket = None
        self.host_key = self._generate_host_key()
    
    def _generate_host_key(self):
        key_path = 'data/ssh_host_rsa_key'
        if os.path.exists(key_path):
            return paramiko.RSAKey.from_private_key_file(key_path)
        else:
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(key_path)
            return key
    
    def handle_client(self, client_socket, client_addr):
        client_ip = client_addr[0]
        client_port = client_addr[1]
        
        if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
            self.logger.warning(f"Blocked SSH connection attempt from {client_ip}:{client_port}")
            client_socket.close()
            return
        
        if self.rate_limiter and self.rate_limiter.should_tarpit(client_ip):
            self.logger.warning(f"Tarpitting SSH connection from {client_ip}:{client_port}")
            time.sleep(30)
            client_socket.close()
            return
        
        try:
            transport = paramiko.Transport(client_socket)
            transport.local_version = self.banner
            transport.add_server_key(self.host_key)
            
            handler = SSHHoneypotHandler(client_ip, self.logger, self.database, self.rate_limiter)
            transport.start_server(server=handler)
            
            self.logger.info(f"SSH connection from {client_ip}:{client_port}")
            self.database.log_connection(client_ip, client_port, 'ssh', 'TCP', 'connected')
            
            if self.rate_limiter:
                if not self.rate_limiter.record_connection(client_ip):
                    self.logger.warning(f"IP {client_ip} blocked due to excessive connections")
            
            channel = transport.accept(30)
            if channel:
                channel.close()
            
        except Exception as e:
            self.logger.error(f"SSH handler error for {client_ip}: {e}")
        finally:
            self.database.log_connection(client_ip, client_port, 'ssh', 'TCP', 'disconnected')
            client_socket.close()
    
    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            self.logger.info(f"SSH honeypot listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"SSH server error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start SSH server: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error stopping SSH server: {e}")
    
    def is_running(self):
        return self.running