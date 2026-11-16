import time
from fastapi import Request, HTTPException, status

class TokenBucketLimiter:
    """
    Thread-safe in-memory Token Bucket rate limiter.
    """
    def __init__(self, rate: float, capacity: float):
        self.rate = rate          # replenishment rate (tokens/sec)
        self.capacity = capacity  # bucket size
        self.buckets = {}         # key -> [tokens, last_update]

    def check(self, key: str):
        now = time.time()
        if key not in self.buckets:
            self.buckets[key] = [self.capacity, now]

        tokens, last_update = self.buckets[key]
        
        # Calculate elapsed time and tokens to add
        elapsed = now - last_update
        replenished = elapsed * self.rate
        tokens = min(self.capacity, tokens + replenished)
        self.buckets[key][1] = now

        if tokens >= 1.0:
            self.buckets[key][0] = tokens - 1.0
            return True
        else:
            self.buckets[key][0] = tokens
            return False

# Global limiters
# 1. Verification limiter: max 5 requests, refilling 1 per 2 seconds (0.5/sec)
auth_limiter = TokenBucketLimiter(rate=0.5, capacity=5.0)

# 2. Quiz generation/submission limiter: max 3 requests, refilling 1 per 5 seconds (0.2/sec)
quiz_limiter = TokenBucketLimiter(rate=0.2, capacity=3.0)

def rate_limit_auth(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not auth_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Auth requests rate limit exceeded. Please wait a moment."
        )

def rate_limit_quiz(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not quiz_limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quiz request rate limit exceeded. Please space out your requests."
        )
