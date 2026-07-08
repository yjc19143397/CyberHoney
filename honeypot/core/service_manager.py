import threading
import time

class ServiceManager:
    def __init__(self, config, logger, database, rate_limiter=None):
        self.config = config
        self.logger = logger
        self.database = database
        self.rate_limiter = rate_limiter
        self.services = {}
        self.running = False
        self.threads = []
    
    def register_service(self, name, service):
        self.services[name] = service
        self.logger.info(f"Registered service: {name}")
    
    def start_service(self, name):
        if name not in self.services:
            self.logger.error(f"Service {name} not found")
            return False
        
        if self.config.get(f'services.{name}.enabled', True):
            try:
                thread = threading.Thread(target=self.services[name].start, daemon=True)
                thread.start()
                self.threads.append(thread)
                self.logger.info(f"Started service: {name}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to start service {name}: {e}")
        return False
    
    def stop_service(self, name):
        if name not in self.services:
            self.logger.error(f"Service {name} not found")
            return False
        
        try:
            self.services[name].stop()
            self.logger.info(f"Stopped service: {name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop service {name}: {e}")
            return False
    
    def start_all(self):
        self.running = True
        for name, service in self.services.items():
            if self.config.get(f'services.{name}.enabled', True):
                try:
                    thread = threading.Thread(target=service.start, daemon=True)
                    thread.start()
                    self.threads.append(thread)
                    self.logger.info(f"Started service: {name}")
                except Exception as e:
                    self.logger.error(f"Failed to start service {name}: {e}")
    
    def stop_all(self):
        self.running = False
        for name, service in self.services.items():
            try:
                service.stop()
                self.logger.info(f"Stopped service: {name}")
            except Exception as e:
                self.logger.error(f"Failed to stop service {name}: {e}")
        
        for thread in self.threads:
            thread.join(timeout=5)
    
    def is_running(self):
        return self.running
    
    def get_service_status(self, name):
        if name in self.services:
            return self.services[name].is_running()
        return False
    
    def get_all_status(self):
        status = {}
        for name, service in self.services.items():
            status[name] = {
                'running': service.is_running(),
                'port': self.config.get(f'services.{name}.port', 0)
            }
        return status