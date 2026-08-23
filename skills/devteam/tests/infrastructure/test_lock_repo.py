import threading

from devteam.domain.locks.policy import CONFLICT, GRANT
from devteam.infrastructure.paths import PathResolver
from devteam.infrastructure.repositories.lock_repo import FileLockRepository

NOW = "2026-01-01T12:00:00"


def _repo(root):
    return FileLockRepository(PathResolver(root))


def test_acquire_get_release(tmp_path):
    r = _repo(str(tmp_path))
    action, lock = r.acquire("src/x.py", "a", "", "", False, NOW)
    assert action == GRANT and lock.holder == "a"
    assert r.get("src/x.py").holder == "a"
    assert [x.path for x in r.all()] == ["src/x.py"]
    assert r.release("src/x.py", "a", False) is True
    assert r.get("src/x.py") is None


def test_release_wrong_holder_refused(tmp_path):
    r = _repo(str(tmp_path))
    r.acquire("p", "a", "", "", False, NOW)
    assert r.release("p", "b", False) is False
    assert r.release("p", "b", True) is True  # force steal-release


def test_concurrent_acquire_one_winner(tmp_path):
    r = _repo(str(tmp_path))
    results: list[str] = []
    lock = threading.Lock()
    barrier = threading.Barrier(12)

    def worker(wid):
        barrier.wait()
        action, _ = r.acquire("shared/file", f"seat-{wid}", "", "", False, NOW)
        with lock:
            results.append(action)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count(GRANT) == 1
    assert results.count(CONFLICT) == 11
