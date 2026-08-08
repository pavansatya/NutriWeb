"""Concurrency tests.

Streamlit serves every user session on its own thread. A DuckDB connection is
not safe to share across threads: two threads interleaving execute() and
fetchdf() consume each other's result sets, which shows up as sporadic None
results rather than a clean error.

That bug was real -- 11 of 12 simulated concurrent users failed -- and it would
only have appeared once two people used the deployed Space at the same time.
These tests keep it fixed.
"""

from __future__ import annotations

import threading

import pytest

from nutriweb.data import catalog
from nutriweb.profile.model import UserProfile
from nutriweb.reco import engine

pytestmark = pytest.mark.skipif(
    not catalog.DEFAULT_CATALOG.exists(),
    reason="catalog not built; run pipeline/01..03 first",
)

QUERIES = ["yogurt", "cereal", "chips", "soda", "bread", "cheese"]


def run_concurrently(worker, count: int) -> list[str]:
    """Run `worker(i)` on `count` threads, returning collected error strings."""
    errors: list[str] = []
    lock = threading.Lock()

    def wrapped(index: int) -> None:
        try:
            worker(index)
        except Exception as exc:  # noqa: BLE001 - we want any failure reported
            with lock:
                errors.append(f"thread {index}: {type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=wrapped, args=(i,)) for i in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=180)
    return errors


class TestThreadSafety:
    def test_each_thread_gets_its_own_cursor(self):
        """Two threads must not share one cursor, or results interleave.

        The cursor objects are kept alive in `cursors` for the duration of the
        assertion. Comparing bare id() values would be flaky: once a worker
        thread exits its thread-local cursor can be collected, and CPython
        happily reuses the freed address for the next thread's cursor.
        """
        catalog.connect()  # warm the shared database handle
        cursors: list = []
        lock = threading.Lock()

        def worker(_: int) -> None:
            con = catalog.connect()
            with lock:
                cursors.append(con)  # holding a reference prevents id reuse

        assert not run_concurrently(worker, 8)
        assert len(cursors) == 8
        assert len({id(c) for c in cursors}) == 8, "threads shared a cursor"

    def test_concurrent_searches_all_return_results(self):
        catalog.connect()

        def worker(i: int) -> None:
            for _ in range(3):
                results = catalog.search(QUERIES[i % len(QUERIES)], 8)
                assert results, "search returned nothing under concurrency"
                assert results[0].get("code")

        assert not run_concurrently(worker, 12)

    def test_concurrent_recommendations_do_not_interleave(self):
        """The original failure: fetchdf() returned None for most threads."""
        catalog.connect()

        def worker(i: int) -> None:
            hits = catalog.search(QUERIES[i % len(QUERIES)], 5)
            assert hits
            for hit in hits[:2]:
                engine.recommend(hit, UserProfile(allergens=["en:milk"]), top_n=5)

        assert not run_concurrently(worker, 12)

    def test_distinct_profiles_do_not_leak_between_threads(self):
        """One user's allergen filter must not affect another's results."""
        catalog.connect()
        product = catalog.search("cheese", 1)[0]
        results: dict[int, set[str]] = {}
        lock = threading.Lock()

        def worker(i: int) -> None:
            profile = (
                UserProfile(allergens=["en:milk"]) if i % 2 else UserProfile()
            )
            recs, _ = engine.recommend(product, profile, top_n=6)
            with lock:
                results[i] = {r.product["code"] for r in recs}

        assert not run_concurrently(worker, 8)

        # Every filtered thread must agree with every other filtered thread.
        filtered = [v for k, v in results.items() if k % 2]
        assert all(v == filtered[0] for v in filtered), "filtered results varied by thread"
        unfiltered = [v for k, v in results.items() if not k % 2]
        assert all(v == unfiltered[0] for v in unfiltered), "unfiltered results varied"
