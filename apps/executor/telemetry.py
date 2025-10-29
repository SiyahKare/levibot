from prometheus_client import Counter, Histogram

REQS = Counter("levi_requests_total", "reqs", ["route"])
LAT = Histogram("levi_latency_seconds", "lat", ["route"])
