"""Shared slowapi limiter singleton.

main.py registers this instance on app.state so the @limiter.limit
decorator finds the same state regardless of where it's imported from.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
