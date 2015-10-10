# -*- coding: utf-8 -*-

import contextlib

class FunctionInfo(object):
    def __init__(self, interactive):
        self.interactive = interactive

_ui_functions = {
    'echo_via_pager': FunctionInfo(interactive=True),
    'prompt': FunctionInfo(interactive=True),
    'confirm': FunctionInfo(interactive=True),
    'clear': FunctionInfo(interactive=False),
    'echo': FunctionInfo(interactive=False),
    'edit': FunctionInfo(interactive=True),
    'launch': FunctionInfo(interactive=True),
    'getchar': FunctionInfo(interactive=True),
    'pause': FunctionInfo(interactive=True),
}


@contextlib.contextmanager
def patch_ui_functions(wrapper):
    '''Wrap all termui functions with a custom decorator.'''
    NONE = object()
    saved = {}
    import click

    for name, info in _ui_functions.items():
        orig = getattr(click, name, NONE)
        if orig is not NONE:
            saved[name] = orig
            setattr(click, name, wrapper(orig, info))

    try:
        yield
    finally:
        for name, orig in saved.items():
            setattr(click, name, orig)
