#!/usr/bin/env python3
"""Clear Redis queues."""

import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Clear all keys
result = r.flushall()
print(f"Redis cleared: {result}")

# Check if it's empty
keys = r.keys('*')
print(f"Remaining keys: {len(keys)}")