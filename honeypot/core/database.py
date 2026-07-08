from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class ConnectionLog(Base):
    __tablename__ = 'connection_logs'
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(50))
    source_port = Column(Integer)
    service = Column(String(20))
    protocol = Column(String(10))
    status = Column(String(20))
    timestamp = Column(DateTime, default=datetime.now)

class CredentialAttempt(Base):
    __tablename__ = 'credential_attempts'
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(50))
    service = Column(String(20))
    username = Column(String(100))
    password = Column(String(200))
    success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)

class HTTPRequest(Base):
    __tablename__ = 'http_requests'
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(50))
    method = Column(String(10))
    path = Column(String(500))
    headers = Column(Text)
    body = Column(Text)
    user_agent = Column(String(500))
    status_code = Column(Integer)
    timestamp = Column(DateTime, default=datetime.now)

class FileTransfer(Base):
    __tablename__ = 'file_transfers'
    id = Column(Integer, primary_key=True)
    source_ip = Column(String(50))
    service = Column(String(20))
    filename = Column(String(500))
    transfer_type = Column(String(10))
    timestamp = Column(DateTime, default=datetime.now)

class Database:
    def __init__(self, config):
        db_path = config.get('database.path', 'data/honeypot.db')
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def log_connection(self, source_ip, source_port, service, protocol, status):
        session = self.Session()
        try:
            log = ConnectionLog(
                source_ip=source_ip,
                source_port=source_port,
                service=service,
                protocol=protocol,
                status=status
            )
            session.add(log)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    
    def log_credential_attempt(self, source_ip, service, username, password, success=False):
        session = self.Session()
        try:
            attempt = CredentialAttempt(
                source_ip=source_ip,
                service=service,
                username=username,
                password=password,
                success=success
            )
            session.add(attempt)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    
    def log_http_request(self, source_ip, method, path, headers, body, user_agent, status_code):
        session = self.Session()
        try:
            import json
            req = HTTPRequest(
                source_ip=source_ip,
                method=method,
                path=path,
                headers=json.dumps(headers),
                body=body,
                user_agent=user_agent,
                status_code=status_code
            )
            session.add(req)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    
    def log_file_transfer(self, source_ip, service, filename, transfer_type):
        session = self.Session()
        try:
            transfer = FileTransfer(
                source_ip=source_ip,
                service=service,
                filename=filename,
                transfer_type=transfer_type
            )
            session.add(transfer)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    
    def get_connection_logs(self, limit=100):
        session = self.Session()
        try:
            return session.query(ConnectionLog).order_by(ConnectionLog.timestamp.desc()).limit(limit).all()
        finally:
            session.close()
    
    def get_credential_attempts(self, limit=100):
        session = self.Session()
        try:
            return session.query(CredentialAttempt).order_by(CredentialAttempt.timestamp.desc()).limit(limit).all()
        finally:
            session.close()
    
    def get_http_requests(self, limit=100):
        session = self.Session()
        try:
            return session.query(HTTPRequest).order_by(HTTPRequest.timestamp.desc()).limit(limit).all()
        finally:
            session.close()
    
    def close(self):
        self.engine.dispose()