from .config import Config
from .logger import Logger
from .database import Database
from .service_manager import ServiceManager
from .rate_limiter import RateLimiter

class Honeypot:
    def __init__(self, config_path="config.yaml"):
        self.config = Config(config_path)
        self.logger = Logger(self.config)
        self.database = Database(self.config)
        self.rate_limiter = RateLimiter(self.config)
        self.service_manager = ServiceManager(self.config, self.logger, self.database, self.rate_limiter)
        self._load_services()
    
    def _load_services(self):
        try:
            from honeypot.services.ssh.server import SSHServer
            from honeypot.services.ftp.server import FTPServer
            from honeypot.services.http.server import HTTPServer
            from honeypot.services.tcp.server import TCPServer
            from honeypot.services.udp.server import UDPServer
            from honeypot.services.telnet.server import TelnetServer
            
            ssh_server = SSHServer(self.config, self.logger, self.database, self.rate_limiter)
            ftp_server = FTPServer(self.config, self.logger, self.database, self.rate_limiter)
            http_server = HTTPServer(self.config, self.logger, self.database, self.rate_limiter)
            tcp_server = TCPServer(self.config, self.logger, self.database, self.rate_limiter)
            udp_server = UDPServer(self.config, self.logger, self.database, self.rate_limiter)
            telnet_server = TelnetServer(self.config, self.logger, self.database, self.rate_limiter)
            
            self.service_manager.register_service('ssh', ssh_server)
            self.service_manager.register_service('ftp', ftp_server)
            self.service_manager.register_service('http', http_server)
            self.service_manager.register_service('tcp', tcp_server)
            self.service_manager.register_service('udp', udp_server)
            self.service_manager.register_service('telnet', telnet_server)
            
            if self.config.get('api.enabled', True):
                from honeypot.api.server import APIServer
                api_server = APIServer(self)
                self.service_manager.register_service('api', api_server)
        except Exception as e:
            self.logger.error(f"Failed to load services: {e}")
    
    def start(self):
        self.logger.info(f"Starting {self.config.get('honeypot.name', 'CyberHoney')} honeypot...")
        self.service_manager.start_all()
        self.logger.info("Honeypot is running. Press Ctrl+C to stop.")
    
    def stop(self):
        self.logger.info("Stopping honeypot...")
        self.service_manager.stop_all()
        self.database.close()
        self.logger.info("Honeypot has been stopped.")
    
    def get_status(self):
        return self.service_manager.get_all_status()