import logging
from logging.handlers import RotatingFileHandler
import os

class Logger:
    def __init__(self, config):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        logger = logging.getLogger('honeypot')
        logger.setLevel(logging.DEBUG)
        
        log_level = self.config.get('logging.level', 'INFO')
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        log_file = self.config.get('logging.file', 'logs/honeypot.log')
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        max_size = self.config.get('logging.max_size', 10485760)
        backup_count = self.config.get('logging.backup_count', 5)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def debug(self, message):
        self.logger.debug(message)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)