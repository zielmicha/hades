import string

def valid_name(s):
    if s.startswith('-') or s.startswith('.'):
        raise ValueError('bad name %r' % s)
    if not all( ch in string.ascii_letters + string.digits + '.-' for ch in s ):
        raise ValueError('bad name %r' % s)

    return True
