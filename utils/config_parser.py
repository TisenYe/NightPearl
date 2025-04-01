import configparser
from threading import Lock

class SingletonConfig:
    _instance = None
    _lock = Lock()
    
    def __new__(cls, file_path):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.parser = configparser.ConfigParser()
                cls._instance.parser.read(file_path)
            return cls._instance
    
    def __getattr__(self, section):
        if self.parser.has_section(section):
            return type('Section', (), dict(self.parser.items(section)))
        raise AttributeError(f"Section {section} not found")

