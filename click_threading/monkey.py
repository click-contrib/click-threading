# -*- coding: utf-8 -*-

import contextlib


_ui_functions = (
    'echo_via_pager',
    'prompt',
    'confirm',
    'clear',
    'edit',
    'launch',
    'getchar',
    'pause',
)


@contextlib.contextmanager
def patch_ui_functions(wrapper):
    '''Wrap all termui functions with a custom decorator.'''
    NONE = object()
    saved = {}
    import click

    for name in _ui_functions:
        orig = getattr(click, name, NONE)
        if orig is not NONE:
            saved[name] = orig
            setattr(click, name, wrapper(orig))

    try:
        yield
    finally:
        for name, orig in saved.items():
            setattr(click, name, orig)
