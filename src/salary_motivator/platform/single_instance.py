"""Per-user process lock shared by login startup and manual launches."""
import os
from ..model import CONFIG

_INSTANCE_LOCK = None


def acquire_instance():
    """Keep login startup and manual launches from opening duplicate counters."""
    global _INSTANCE_LOCK
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    handle = (CONFIG.parent / "instance.lock").open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return False
    _INSTANCE_LOCK = handle
    return True


def release_instance():
    global _INSTANCE_LOCK
    if _INSTANCE_LOCK is not None:
        _INSTANCE_LOCK.close()
        _INSTANCE_LOCK = None
