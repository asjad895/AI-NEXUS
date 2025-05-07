
import logging
from logging.config import dictConfig

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "faq_pipeline.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "level": "INFO"
        }
    },
    "loggers": {
        "faq_pipeline": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}

dictConfig(logging_config)
logger = logging.getLogger("faq_pipeline")