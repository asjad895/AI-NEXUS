"""
Prometheus metrics middleware for monitoring API performance.
"""

import time
from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client.exposition import generate_latest
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

# Define metrics
REQUEST_COUNT = Counter(
    'api_request_count', 
    'Number of requests received', 
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds', 
    'Request latency in seconds', 
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'api_active_requests', 
    'Number of active requests', 
    ['method', 'endpoint']
)

PROCESSING_JOBS = Gauge(
    'api_processing_jobs', 
    'Number of jobs currently processing'
)

JOB_PROCESSING_TIME = Summary(
    'api_job_processing_time_seconds', 
    'Time spent processing jobs',
    ['status']
)

ERROR_COUNT = Counter(
    'api_error_count', 
    'Number of errors occurred', 
    ['method', 'endpoint', 'error_type']
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        
        # Skip metrics endpoint to avoid recursion
        if path == "/metrics":
            return await call_next(request)
        
        # Track request count and latency
        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Update metrics
            REQUEST_COUNT.labels(method=method, endpoint=path, http_status=status_code).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(time.time() - start_time)
            
            return response
        except Exception as e:
            # Track exceptions
            ERROR_COUNT.labels(method=method, endpoint=path, error_type=type(e).__name__).inc()
            raise e
        finally:
            ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()

async def metrics_endpoint():
    """
    Endpoint to expose Prometheus metrics.
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )