# -*- coding: utf-8 -*-

import sys
import queue
import threading
import functools
import click

from ._compat import reraise

__version__ = '0.1.0'


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
    def __init__(self):
        if not _is_main_thread():
            raise RuntimeError('The UiWorker can only run on the main thread.')

        self.tasks = queue.Queue()
        self.results = queue.Queue()

    def work(self):
        try:
            func = self.tasks.get()
        except queue.Empty:
            return

        try:
            result = func()
            exc_info = None
        except BaseException:
            exc_info = sys.exc_info()
            result = None

        self.results.put((func, result, exc_info))

    def put(self, func):
        self.tasks.put(func)
        orig_func, result, exc_info = self.results.get()

        if orig_func is not func:
            raise RuntimeError('Got the wrong result.')

        if exc_info is not None:
            reraise(*exc_info)

        return result

    def patch_click(self):
        from .monkey import patch_ui_functions

        def wrapper(f):
            @functools.wraps(f)
            def inner(*a, **kw):
                return self.put(lambda: f(*a, **kw))
            return inner

        return patch_ui_functions(wrapper)
