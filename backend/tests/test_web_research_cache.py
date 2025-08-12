import time

from tools.web_research.cache import TTLCache


def test_ttlcache_hits_misses_eviction():
    c = TTLCache(max_items=2, ttl_s=1)
    assert c.get('a') is None
    c.set('a', 1)
    assert c.get('a') == 1
    c.set('b', 2)
    c.set('c', 3)  # evict oldest (a)
    assert c.get('a') is None
    s = c.stats()
    assert s['evictions'] >= 1
    time.sleep(1.1)
    assert c.get('b') is None  # expired
