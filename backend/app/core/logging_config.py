import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = getattr(record, 'request_id')
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = getattr(record, 'user_id')
        
        if hasattr(record, 'task_id'):
            log_entry['task_id'] = getattr(record, 'task_id')
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

def get_logging_config(log_level: str = "INFO", enable_file_logging: bool = True) -> Dict[str, Any]:
    """Get logging configuration dictionary"""
    
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                '()': JSONFormatter,
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'stream': sys.stdout
            }
        },
        'loggers': {
            'app': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'celery': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        }
    }
    
    if enable_file_logging:
        config['handlers'].update({
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'json',
                'filename': '/app/logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filename': '/app/logs/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
        })
        
        for logger_name in ['app', 'uvicorn', 'celery']:
            config['loggers'][logger_name]['handlers'].extend(['file', 'error_file'])

    return config

def setup_logging(log_level: str = "INFO", enable_file_logging: bool = True):
    """Configure the logging system"""
    config = get_logging_config(log_level, enable_file_logging)
    logging.config.dictConfig(config)
    
    setup_request_context()

def setup_request_context():
    """Set up request context for logging"""
    import contextvars
    
    request_id_var = contextvars.ContextVar('request_id', default=None)
    user_id_var = contextvars.ContextVar('user_id', default=None)
    task_id_var = contextvars.ContextVar('task_id', default=None)
    
    import sys
    current_module = sys.modules[__name__]
    setattr(current_module, 'request_id_var', request_id_var)
    setattr(current_module, 'user_id_var', user_id_var)
    setattr(current_module, 'task_id_var', task_id_var)

class ContextualLogger:
    """Logger that includes contextual information"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _add_context(self, extra: Optional[dict] = None) -> dict:
        """Add contextual information to log record"""
        context = extra or {}
        
        try:
            import sys
            current_module = sys.modules[__name__]
            
            if hasattr(current_module, 'request_id_var'):
                request_id = current_module.request_id_var.get()
                if request_id:
                    context['request_id'] = request_id
            
            if hasattr(current_module, 'user_id_var'):
                user_id = current_module.user_id_var.get()
                if user_id:
                    context['user_id'] = user_id
            
            if hasattr(current_module, 'task_id_var'):
                task_id = current_module.task_id_var.get()
                if task_id:
                    context['task_id'] = task_id
        except:
            pass
        
        return context
    
    def debug(self, message: str, extra: Optional[dict] = None):
        self.logger.debug(message, extra=self._add_context(extra))
    
    def info(self, message: str, extra: Optional[dict] = None):
        self.logger.info(message, extra=self._add_context(extra))
    
    def warning(self, message: str, extra: Optional[dict] = None):
        self.logger.warning(message, extra=self._add_context(extra))
    
    def error(self, message: str, extra: Optional[dict] = None):
        self.logger.error(message, extra=self._add_context(extra))
    
    def critical(self, message: str, extra: Optional[dict] = None):
        self.logger.critical(message, extra=self._add_context(extra))

def get_logger(name: str) -> ContextualLogger:
    """Get a contextual logger instance"""
    return ContextualLogger(name)
