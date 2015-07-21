# -*- coding: utf-8 -*-

import sys

PY2 = sys.version_info[0] == 2

if PY2:
    exec('def reraise(tp, value, tb=None):\n raise tp, value, tb')
else:
    def reraise(tp, value, tb=None):
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value
