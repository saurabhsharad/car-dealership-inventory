import threading
from collections.abc import Callable


def run_concurrently[S, T](
    count: int, prepare: Callable[[], S], act: Callable[[S], T]
) -> list[T]:
    """Run act in count threads at the same moment and return their results.

    Each thread calls prepare() first (for example, to open its database
    connection), then waits at a barrier so every act() starts together.
    Slow setup cannot then serialise the race. An exception in any thread
    is re-raised.
    """
    barrier = threading.Barrier(count)
    results: list[T | BaseException | None] = [None] * count

    def worker(index: int) -> None:
        try:
            prepared = prepare()
            barrier.wait()
            results[index] = act(prepared)
        except BaseException as error:
            barrier.abort()
            results[index] = error

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for result in results:
        if isinstance(result, BaseException):
            raise result
    return results
