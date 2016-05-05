import string

def valid_name(s):
    return all( ch in string.ascii_letters + string.digits + '.-' for ch in s ) and s not in ('.', '..')
