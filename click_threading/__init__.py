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

__version__ = '0.2.0'

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
        self.results = queue.Queue()

    def shutdown(self):
        self.put(self.SHUTDOWN, wait=False)

    def run(self):
        while True:
            func, need_result = self.tasks.get()
            if func is self.SHUTDOWN:
                return

            try:
                result = func()
                exc_info = None
            except BaseException:
                exc_info = sys.exc_info()
                result = None

            if need_result:
                self.results.put((func, result, exc_info))

    def put(self, func, wait=True):
        self.tasks.put((func, wait))
        if not wait:
            return
        orig_func, result, exc_info = self.results.get()

        if orig_func is not func:
            raise RuntimeError('Got the wrong result.')

        if exc_info is not None:
            reraise(*exc_info)

        return result

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
