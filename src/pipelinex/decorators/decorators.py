from importlib.util import find_spec
import logging
import time
from functools import wraps
from typing import Callable

log = logging.getLogger(__name__)


def _func_full_name(func: Callable):
    return getattr(func, "__qualname__", repr(func))


def _human_readable_time(elapsed: float):  # pragma: no cover
    mins, secs = divmod(elapsed, 60)
    hours, mins = divmod(mins, 60)

    if hours > 0:
        message = "%dh%02dm%02ds" % (hours, mins, secs)
    elif mins > 0:
        message = "%dm%02ds" % (mins, secs)
    elif secs >= 1:
        message = "%.2fs" % secs
    else:
        message = "%.0fms" % (secs * 1000.0)

    return message


def log_time(func: Callable) -> Callable:
    """A function decorator which logs the time taken for executing a function.

    Args:
        func: The function to be logged.

    Returns:
        A wrapped function, which will execute the provided function and log
        the running time.

    """

    @wraps(func)
    def with_time(*args, **kwargs):
        log = logging.getLogger(__name__)
        t_start = time.time()
        result = func(*args, **kwargs)
        t_end = time.time()
        elapsed = t_end - t_start

        log.info(
            "Running %r took %s [%.3fs]",
            _func_full_name(func),
            _human_readable_time(elapsed),
            elapsed,
        )
        return result

    return with_time


if find_spec("memory_profiler"):
    from memory_profiler import memory_usage

    def mem_profile(func: Callable) -> Callable:
        """A function decorator which profiles the memory used when executing the
        function. The logged memory is collected by using the memory_profiler
        python module and includes memory used by children processes. The usage
        is collected by taking memory snapshots every 100ms. This decorator will
        only work with functions taking at least 0.5s to execute due to a bug in
        the memory_profiler python module. For more information about the bug,
        please see https://github.com/pythonprofilers/memory_profiler/issues/216

        Args:
            func: The function to be profiled.

        Returns:
            A wrapped function, which will execute the provided function and log
            its max memory usage upon completion.

        """

        @wraps(func)
        def with_memory(*args, **kwargs):
            log = logging.getLogger(__name__)
            mem_usage, result = memory_usage(
                (func, args, kwargs),
                interval=0.1,
                timeout=1,
                max_usage=True,
                retval=True,
                include_children=True,
            )
            log.info(
                "Running %r consumed %2.2fMiB memory at peak time",
                _func_full_name(func),
                mem_usage[0],
            )
            return result

        return with_memory


def dict_of_list_to_list_of_dict(dict_of_list):
    return [
        dict(zip(dict_of_list.keys(), vals)) for vals in zip(*dict_of_list.values())
    ]


def dict_io(func: Callable) -> Callable:
    @wraps(func)
    def _dict_io(*args):
        keys = args[0].keys()

        out_dict = {}
        for key in keys:
            a = [e.get(key) for e in args]
            out = func(*a)
            out_dict[key] = out
            log.info("{}: {}".format(key, out))

        if isinstance(out_dict[key], tuple):
            return tuple(dict_of_list_to_list_of_dict(out_dict))

        else:
            return out_dict

    return _dict_io
