from flask import Flask, jsonify, request
import threading

class APIServer:
    def __init__(self, honeypot):
        self.honeypot = honeypot
        self.config = honeypot.config
        self.logger = honeypot.logger
        self.database = honeypot.database
        self.host = self.config.get('api.host', '127.0.0.1')
        self.port = self.config.get('api.port', 5000)
        self.running = False
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/api/health', methods=['GET'])
        def health():
            return jsonify({'status': 'ok', 'services': self.honeypot.get_service_status()})
        
        @self.app.route('/api/attacks', methods=['GET'])
        def get_attacks():
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            attacks = self.database.get_attacks(limit, offset)
            return jsonify({'attacks': attacks})
        
        @self.app.route('/api/connections', methods=['GET'])
        def get_connections():
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            connections = self.database.get_connections(limit, offset)
            return jsonify({'connections': connections})
        
        @self.app.route('/api/credentials', methods=['GET'])
        def get_credentials():
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            credentials = self.database.get_credential_attempts(limit, offset)
            return jsonify({'credentials': credentials})
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            stats = self.database.get_stats()
            return jsonify(stats)
        
        @self.app.route('/api/services', methods=['GET'])
        def get_services():
            services = self.honeypot.get_service_status()
            return jsonify({'services': services})
        
        @self.app.route('/api/services/<service>/start', methods=['POST'])
        def start_service(service):
            result = self.honeypot.start_service(service)
            return jsonify({'success': result})
        
        @self.app.route('/api/services/<service>/stop', methods=['POST'])
        def stop_service(service):
            result = self.honeypot.stop_service(service)
            return jsonify({'success': result})
        
        @self.app.route('/api/blocked_ips', methods=['GET'])
        def get_blocked_ips():
            blocked = self.honeypot.rate_limiter.get_blocked_ips()
            return jsonify({'blocked_ips': blocked})
        
        @self.app.route('/api/unblock/<ip>', methods=['POST'])
        def unblock_ip(ip):
            result = self.honeypot.rate_limiter.unblock_ip(ip)
            return jsonify({'success': result})
    
    def start(self):
        self.running = True
        try:
            self.app.run(host=self.host, port=self.port, threaded=True)
            self.logger.info(f"API server listening on {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            self.running = False
    
    def stop(self):
        self.running = False
    
    def is_running(self):
        return self.running