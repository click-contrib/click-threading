# -*- coding: utf-8 -*-


_ui_functions = (
    'echo',
    'echo_via_pager',
    'prompt',
    'confirm',
    'clear',
    'edit',
    'launch',
    'getchar',
    'pause',
)

saved = {}


def patch_ui_functions(wrapper):
    '''Wrap all termui functions with a custom decorator.'''
    NONE = object()
    import click

    for name in _ui_functions:
        orig = getattr(click, name, NONE)
        if orig is not NONE:
            orig = saved.setdefault(name, orig)
            setattr(click, name, wrapper(orig))
