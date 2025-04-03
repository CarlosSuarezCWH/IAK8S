import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, 'request'):
            log_data.update(self._extract_request_data(record.request))

        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)

    def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        return {
            "request": {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client": {
                    "host": request.client.host if request.client else None,
                    "port": request.client.port if request.client else None
                }
            }
        }

class RequestLoggerMiddleware:
    async def __call__(
        self,
        request: Request,
        call_next: RequestResponseEndpoint
    ):
        logger = logging.getLogger("api")
        
        try:
            # Log request
            logger.info(
                "Request received",
                extra={
                    "request": request,
                    "type": "http.request"
                }
            )
            
            response = await call_next(request)
            
            # Log response
            logger.info(
                "Response sent",
                extra={
                    "status_code": response.status_code,
                    "type": "http.response"
                }
            )
            
            return response
        except Exception as e:
            logger.error(
                "Request processing failed",
                exc_info=True,
                extra={
                    "request": request,
                    "type": "http.error"
                }
            )
            raise

def setup_logging(log_level: str = "INFO") -> None:
    """Configura logging estructurado"""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Eliminar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Configurar handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # Configurar logging para librerías específicas
    for lib in ['uvicorn', 'fastapi', 'sqlalchemy']:
        lib_logger = logging.getLogger(lib)
        lib_logger.setLevel("WARNING")
        lib_logger.propagate = True

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Obtiene logger configurado"""
    logger = logging.getLogger(name or "app")
    logger.propagate = True
    return logger

# Ejemplo de uso:
# logger = get_logger(__name__)
# logger.info("Mensaje informativo", extra={"key": "value"})