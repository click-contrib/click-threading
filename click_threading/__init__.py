# -*- coding: utf-8 -*-

import sys
import threading
import functools
import contextlib
import click

from ._compat import reraise

try:
    import queue
except ImportError:
    import Queue as queue

# The docs state that "Future should not be instantiated directly, only by
# Executors", but since I'm basically implementing my own executor here, I
# think we're fine.
try:
    from concurrent.futures import Future
except ImportError:
    from futures import Future

__version__ = '0.4.0'

_CTX_WORKER_KEY = __name__ + '.uiworker'


def _is_main_thread(thread=None):
    thread = thread or threading.current_thread()
    return type(thread).__name__ == '_MainThread'


class Thread(threading.Thread):
    '''A thread that automatically pushes the parent thread's context in the
    new thread.'''

    def __init__(self, *args, **kwargs):
        self._click_context = click.get_current_context()
        super(Thread, self).__init__(*args, **kwargs)

    def run(self):
        with self._click_context:
            return super(Thread, self).run()


class UiWorker(object):
    SHUTDOWN = object()

    def __init__(self):
        if not _is_main_thread():
            raise RuntimeError('The UiWorker can only run on the main thread.')

        self.tasks = queue.Queue()

    def shutdown(self):
        self.put(self.SHUTDOWN, wait=False)

    def run(self):
        while True:
            func, future = self.tasks.get()
            if func is self.SHUTDOWN:
                return

            try:
                result = func()
            except BaseException as e:
                future.set_exception(e)
            else:
                future.set_result(result)

    def put(self, func, wait=True):
        if _is_main_thread():
            return func()

        future = Future()
        self.tasks.put((func, future))
        if not wait:
            return

        return future.result()

    @contextlib.contextmanager
    def patch_click(self):
        from .monkey import patch_ui_functions

        def wrapper(f, info):
            @functools.wraps(f)
            def inner(*a, **kw):
                return get_ui_worker() \
                    .put(lambda: f(*a, **kw), wait=info.interactive)
            return inner

        ctx = click.get_current_context()
        with patch_ui_functions(wrapper):
            ctx.meta[_CTX_WORKER_KEY] = self
            try:
                yield
            finally:
                assert ctx.meta.pop(_CTX_WORKER_KEY) is self


def get_ui_worker():
    try:
        ctx = click.get_current_context()
        return ctx.meta[_CTX_WORKER_KEY]
    except (RuntimeError, KeyError):
        raise RuntimeError('UI worker not found.')
