from tools.web_research.limiter import TokenBucket


def test_token_bucket_allow_pattern():
    tb = TokenBucket(rate_per_s=2.0)
    allowed = [tb.allow() for _ in range(5)]
    assert allowed.count(True) >= 1
    assert allowed.count(False) >= 1
