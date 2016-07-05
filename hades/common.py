import string
import os
import glob
import stat

def valid_name(s):
    if s.startswith('-') or s.startswith('.'):
        raise ValueError('bad name %r' % s)
    if not all( ch in string.ascii_letters + string.digits + '.-' for ch in s ):
        raise ValueError('bad name %r' % s)

    return True

def maybe_mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)

def write_file(path, data):
    fd = os.open(path, os.O_NOFOLLOW | os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0o644)
    if isinstance(data, str):
        data = data.encode('utf8')
    with os.fdopen(fd, 'wb') as f:
        f.write(data)

class Observable:
    def __init__(self, need_return=False):
        self._funcs = []
        self._need_return = need_return

    def register(self, func):
        self._funcs.append(func)
        return func

    def call(self, *args, **kwargs):
        returns = []
        for func in self._funcs:
            returns.append(func(*args, **kwargs))

        if self._need_return:
            if returns.count(None) != len(returns) - 1:
                raise ValueError('bad number of values returned for args=%s kwargs=%s' % (args, kwargs))
            for v in returns:
                if v is not None:
                    return v

def cached_property(func):
    def get(self):
        name = '__cached_' + func.__name__
        try:
            return getattr(self, name)
        except AttributeError:
            val = func(self)
            setattr(self, name, val)
            return val

    return property(get)
