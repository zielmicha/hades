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

def add_devices(definition, pattern, uid=0, gid=0, mode=0o660):
    devices = glob.glob(pattern)
    for dev in devices:
        definition['devices']['dev' + dev.replace('/', '--')] = {
            'type': 'unix-block' if stat.S_ISBLK(os.stat(dev).st_mode) else 'unix-char',
            'path': dev,
            'uid': uid,
            'gid': gid,
            'mode': oct(mode)[2:]
        }
