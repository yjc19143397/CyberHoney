from flask import Flask, request, jsonify, render_template_string
import threading
import os
import time

class HTTPServer:
    def __init__(self, config, logger, database, rate_limiter=None):
        self.config = config
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.host = config.get('honeypot.host', '0.0.0.0')
        self.port = config.get('services.http.port', 8080)
        self.ssl_enabled = config.get('services.http.ssl_enabled', False)
        self.ssl_port = config.get('services.http.ssl_port', 8443)
        self.running = False
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.before_request
        def log_request():
            client_ip = request.remote_addr
            
            if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
                self.logger.warning(f"Blocked HTTP request from {client_ip}")
                return "Service unavailable", 429
            
            if self.rate_limiter and self.rate_limiter.should_tarpit(client_ip):
                self.logger.warning(f"Tarpitting HTTP request from {client_ip}")
                time.sleep(10)
            
            method = request.method
            path = request.path
            headers = dict(request.headers)
            body = request.get_data(as_text=True)
            user_agent = request.headers.get('User-Agent', '')
            
            self.logger.info(f"HTTP {method} request from {client_ip}: {path}")
            self.database.log_http_request(client_ip, method, path, headers, body, user_agent, 200)
            
            if self.rate_limiter:
                self.rate_limiter.record_request(client_ip)
                if not self.rate_limiter.record_connection(client_ip):
                    self.logger.warning(f"IP {client_ip} blocked due to excessive connections")
        
        @self.app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
        def index():
            client_ip = request.remote_addr
            if self.rate_limiter:
                delay = self.rate_limiter.get_delay(client_ip)
                if delay > 0:
                    time.sleep(delay)
            return self._fake_index_page()
        
        @self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS'])
        def catch_all(path):
            client_ip = request.remote_addr
            if self.rate_limiter:
                delay = self.rate_limiter.get_delay(client_ip)
                if delay > 0:
                    time.sleep(delay)
            
            if path.endswith('.php') or path.endswith('.asp') or path.endswith('.jsp'):
                return self._fake_php_page(path), 200
            elif path.endswith('.html') or path.endswith('.htm'):
                return self._fake_html_page(path), 200
            elif path.endswith('.json'):
                return jsonify({'status': 'ok', 'data': {}}), 200
            elif path.endswith('.xml'):
                return '<?xml version="1.0"?><response><status>ok</status></response>', 200, {'Content-Type': 'application/xml'}
            elif path in ['robots.txt', 'sitemap.xml']:
                return '', 200
            else:
                return self._fake_404_page(path), 404
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            client_ip = request.remote_addr
            
            if self.rate_limiter and self.rate_limiter.is_blocked(client_ip):
                return "Service unavailable", 429
            
            if self.rate_limiter:
                delay = self.rate_limiter.get_delay(client_ip)
                if delay > 0:
                    time.sleep(delay)
            
            if request.method == 'POST':
                username = request.form.get('username', '')
                password = request.form.get('password', '')
                self.logger.warning(f"HTTP login attempt from {client_ip}: {username}/{password}")
                self.database.log_credential_attempt(client_ip, 'http', username, password, False)
                
                if self.rate_limiter:
                    if not self.rate_limiter.record_credential_attempt(client_ip):
                        self.logger.warning(f"IP {client_ip} blocked due to excessive credential attempts")
                        return "Service unavailable", 429
                
                return "Login failed", 401
            return self._fake_login_page()
        
        @self.app.route('/admin', methods=['GET', 'POST'])
        def admin():
            client_ip = request.remote_addr
            if self.rate_limiter:
                delay = self.rate_limiter.get_delay(client_ip)
                if delay > 0:
                    time.sleep(delay)
            return self._fake_admin_page()
    
    def _fake_index_page(self):
        html = '''<!DOCTYPE html>
<html>
<head><title>Welcome to Our Server</title></head>
<body>
<h1>Welcome</h1>
<p>This is a test server.</p>
<form action="/login" method="post">
    Username: <input type="text" name="username"><br>
    Password: <input type="password" name="password"><br>
    <input type="submit" value="Login">
</form>
</body>
</html>'''
        return html
    
    def _fake_login_page(self):
        html = '''<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
<h1>Login</h1>
<form action="/login" method="post">
    Username: <input type="text" name="username"><br>
    Password: <input type="password" name="password"><br>
    <input type="submit" value="Login">
</form>
</body>
</html>'''
        return html
    
    def _fake_admin_page(self):
        html = '''<!DOCTYPE html>
<html>
<head><title>Admin Panel</title></head>
<body>
<h1>Admin Panel</h1>
<p>Welcome to the admin panel.</p>
</body>
</html>'''
        return html
    
    def _fake_php_page(self, path):
        return f'<?php echo "This is {path}"; ?>'
    
    def _fake_html_page(self, path):
        return f'<html><body><h1>{path}</h1><p>Page content</p></body></html>'
    
    def _fake_404_page(self, path):
        return f'<html><body><h1>404 Not Found</h1><p>{path} not found</p></body></html>'
    
    def start(self):
        self.running = True
        try:
            if self.ssl_enabled:
                self.app.run(host=self.host, port=self.ssl_port, ssl_context='adhoc', threaded=True)
            else:
                self.app.run(host=self.host, port=self.port, threaded=True)
            self.logger.info(f"HTTP honeypot listening on {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start HTTP server: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
    
    def is_running(self):
        return self.running