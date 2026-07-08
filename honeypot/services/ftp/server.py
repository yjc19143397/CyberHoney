import socket
import threading
import os
import time

class FTPServer:
    def __init__(self, config, logger, database, rate_limiter=None):
        self.config = config
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.host = config.get('honeypot.host', '0.0.0.0')
        self.port = config.get('services.ftp.port', 2121)
        self.banner = config.get('services.ftp.banner', '220 Welcome to FTP Server')
        self.running = False
        self.server_socket = None
        self._fake_files = [
            {'name': 'README.txt', 'size': 1024, 'type': 'file'},
            {'name': 'backup.tar.gz', 'size': 1048576, 'type': 'file'},
            {'name': 'logs/', 'size': 0, 'type': 'dir'},
            {'name': 'config.ini', 'size': 512, 'type': 'file'},
            {'name': 'data/', 'size': 0, 'type': 'dir'},
        ]
    
    def _send_response(self, conn, code, message):
        response = f"{code} {message}\r\n"
        conn.send(response.encode())
    
    def _parse_command(self, line):
        line = line.strip().upper()
        parts = line.split(None, 1)
        cmd = parts[0] if parts else ''
        args = parts[1] if len(parts) > 1 else ''
        return cmd, args
    
    def handle_client(self, client_socket, client_addr):
        client_ip = client_addr[0]
        client_port = client_addr[1]
        
        if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
            self.logger.warning(f"Blocked FTP connection attempt from {client_ip}:{client_port}")
            client_socket.close()
            return
        
        if self.rate_limiter and self.rate_limiter.should_tarpit(client_ip):
            self.logger.warning(f"Tarpitting FTP connection from {client_ip}:{client_port}")
            time.sleep(30)
            client_socket.close()
            return
        
        try:
            self.logger.info(f"FTP connection from {client_ip}:{client_port}")
            self.database.log_connection(client_ip, client_port, 'ftp', 'TCP', 'connected')
            
            if self.rate_limiter:
                if not self.rate_limiter.record_connection(client_ip):
                    self.logger.warning(f"IP {client_ip} blocked due to excessive connections")
            
            conn = client_socket.makefile('rwb')
            self._send_response(conn, 220, self.banner)
            
            authenticated = False
            username = None
            
            while self.running:
                try:
                    line = conn.readline().decode().strip()
                    if not line:
                        break
                    
                    cmd, args = self._parse_command(line)
                    
                    if cmd == 'USER':
                        username = args
                        self._send_response(conn, 331, 'Please specify the password.')
                    elif cmd == 'PASS':
                        password = args
                        
                        if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
                            self._send_response(conn, 421, 'Service not available.')
                            break
                        
                        if self.rate_limiter:
                            delay = self.rate_limiter.get_delay(client_ip)
                            if delay > 0:
                                time.sleep(delay)
                        
                        self.logger.warning(f"FTP authentication attempt from {client_ip}: {username}/{password}")
                        self.database.log_credential_attempt(client_ip, 'ftp', username, password, False)
                        
                        if self.rate_limiter:
                            if not self.rate_limiter.record_credential_attempt(client_ip):
                                self.logger.warning(f"IP {client_ip} blocked due to excessive credential attempts")
                                self._send_response(conn, 421, 'Service not available.')
                                break
                        
                        authenticated = True
                        self._send_response(conn, 230, 'Login successful.')
                    elif cmd == 'QUIT':
                        self._send_response(conn, 221, 'Goodbye.')
                        break
                    elif cmd == 'PWD':
                        self._send_response(conn, 257, '"/"')
                    elif cmd == 'LIST':
                        file_list = "\r\n".join([
                            f"-rwxr-xr-x 1 root root {f['size']} Jan 1 00:00 {f['name']}"
                            for f in self._fake_files
                        ])
                        self._send_response(conn, 150, 'Opening ASCII mode data connection for file list')
                        conn.send(f"{file_list}\r\n".encode())
                        self._send_response(conn, 226, 'Transfer complete.')
                    elif cmd == 'NLST':
                        names = "\r\n".join([f['name'] for f in self._fake_files])
                        self._send_response(conn, 150, 'Opening ASCII mode data connection for file list')
                        conn.send(f"{names}\r\n".encode())
                        self._send_response(conn, 226, 'Transfer complete.')
                    elif cmd == 'RETR':
                        filename = args.strip()
                        self.logger.warning(f"FTP file download attempt from {client_ip}: {filename}")
                        self.database.log_file_transfer(client_ip, 'ftp', filename, 'download')
                        self._send_response(conn, 150, 'Opening ASCII mode data connection')
                        conn.send(b"Fake file content for " + filename.encode() + b"\r\n")
                        self._send_response(conn, 226, 'Transfer complete.')
                    elif cmd == 'STOR':
                        filename = args.strip()
                        self.logger.warning(f"FTP file upload attempt from {client_ip}: {filename}")
                        self.database.log_file_transfer(client_ip, 'ftp', filename, 'upload')
                        self._send_response(conn, 150, 'Opening ASCII mode data connection')
                        data = b''
                        while True:
                            chunk = conn.read(1024)
                            if not chunk:
                                break
                            data += chunk
                        self._send_response(conn, 226, 'Transfer complete.')
                    elif cmd == 'CWD':
                        self._send_response(conn, 250, 'Directory successfully changed.')
                    elif cmd == 'CDUP':
                        self._send_response(conn, 200, 'Command okay.')
                    elif cmd == 'TYPE':
                        self._send_response(conn, 200, 'Type set to ASCII.')
                    elif cmd == 'PORT':
                        self._send_response(conn, 200, 'Port command successful.')
                    elif cmd == 'PASV':
                        self._send_response(conn, 227, 'Entering Passive Mode (127,0,0,1,10,0)')
                    else:
                        self._send_response(conn, 500, 'Unknown command.')
                        
                except Exception as e:
                    self.logger.error(f"FTP command error for {client_ip}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"FTP handler error for {client_ip}: {e}")
        finally:
            self.database.log_connection(client_ip, client_port, 'ftp', 'TCP', 'disconnected')
            client_socket.close()
    
    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            self.logger.info(f"FTP honeypot listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_addr = self.server_socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, client_addr), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"FTP server error: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start FTP server: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error stopping FTP server: {e}")
    
    def is_running(self):
        return self.running