from __future__ import annotations

import threading
from concurrent.futures import CancelledError, FIRST_COMPLETED, ThreadPoolExecutor, wait


_work_state = threading.local()


def check_cancelled():
    stop = getattr(_work_state, "stop", None)
    if stop is not None and stop.is_set():
        raise CancelledError("La ejecución se ha interrumpido.")


def bounded_results(function, items, workers):
    if workers == 1:
        for item in items:
            check_cancelled()
            yield function(item)
        return
    iterator = iter(items)
    executor = ThreadPoolExecutor(max_workers=workers)
    stop = getattr(_work_state, "stop", None) or threading.Event()
    pending, failure = set(), None

    def run(item):
        _work_state.stop = stop
        check_cancelled()
        try:
            return function(item)
        except BaseException:
            stop.set()
            raise

    try:
        for _ in range(workers):
            item = next(iterator, None)
            if item is not None:
                pending.add(executor.submit(run, item))
        while pending:
            finished, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in finished:
                try:
                    result = future.result()
                except Exception as error:
                    if failure is None or isinstance(failure, CancelledError):
                        failure = error
                else:
                    yield result
            if failure is None and not stop.is_set():
                for _ in finished:
                    item = next(iterator, None)
                    if item is not None:
                        pending.add(executor.submit(run, item))
        if failure is not None:
            raise failure
        if stop.is_set():
            raise CancelledError("La ejecución se ha interrumpido.")
    finally:
        if pending:
            stop.set()
        for future in pending:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)
