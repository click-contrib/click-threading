# -*- coding: utf-8 -*-

import threading
import click

__version__ = '0.1.0'


class Thread(threading.Thread):
    '''A thread that automatically pushes the parent thread's context in the
    new thread.'''

    def __init__(self, *args, **kwargs):
        self._click_context = click.get_current_context()
        super(Thread, self).__init__(*args, **kwargs)

    def run(self):
        with self._click_context:
            return super(Thread, self).run()
