from datetime import datetime, timezone

from cachetools import TTLCache

class PeriodicCache(TTLCache):
    """
    Special cache memory should be removed every 30 mins
    Should be setted at 1800 (30 mins)
    """


    def __init__(self, maxsize, ttl, getsizeof=None):
        def local_timer():
            ts = datetime.now(timezone.utc).timestamp()
            offset = (ts % ttl)
            return ts - offset 
        
        super().__init__(maxsize=maxsize, ttl=ttl - 1e-5, timer=local_timer, getsizeof=getsizeof)