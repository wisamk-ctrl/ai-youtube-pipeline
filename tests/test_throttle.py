import pytest

from pipeline.ingestion.watch_sources import _Throttle


def test_backs_off_once_then_stops_asking():
    calls, naps = [], []
    def refused(*a):
        calls.append(a)
        raise RuntimeError("429 Client Error: Too Many Requests")
    g = _Throttle(1.0, backoff=20, sleep=naps.append)
    assert g.get(refused, "x") is None and len(calls) == 2 and g.blocked
    assert g.get(refused, "y") is None and len(calls) == 2 and g.skipped == 1
    assert 20 in naps


def test_a_retry_that_works_and_other_errors_pass_through():
    n = {"k": 0}
    def flaky():
        n["k"] += 1
        if n["k"] == 1:
            raise RuntimeError("429")
        return ["ok"]
    g = _Throttle(0, backoff=0, sleep=lambda s: None)
    assert g.get(flaky) == ["ok"] and not g.blocked
    with pytest.raises(ValueError):
        g.get(lambda: (_ for _ in ()).throw(ValueError("bad feed")))
