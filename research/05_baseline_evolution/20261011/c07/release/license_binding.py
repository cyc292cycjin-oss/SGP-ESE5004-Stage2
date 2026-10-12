"""Explicit license path only. Never opens, hashes, copies or parses the license."""
from pathlib import Path
import ctypes as C
import os
import stat
import time

LICENSE_PATH = Path('/root/.config/gurobi/gurobi.lic')


def bind_license():
    p = LICENSE_PATH
    s = p.lstat()  # Reject links; do not follow a replacement credential path.
    if not stat.S_ISREG(s.st_mode) or s.st_uid != 0 or stat.S_IMODE(s.st_mode) & 0o077:
        raise PermissionError('LICENSE_NOT_ROOT_PRIVATE_REGULAR_FILE')
    if not os.access(p, os.R_OK):
        raise PermissionError('LICENSE_NOT_READABLE_BY_WORKER')
    for parent in p.parents:
        st = parent.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or stat.S_IMODE(st.st_mode) & 0o022:
            raise PermissionError('LICENSE_PARENT_NOT_ROOT_CONTROLLED')
    os.environ['GRB_LICENSE_FILE'] = str(p)
    return {'path': str(p), 'exists': True, 'regular_file': True, 'owner_uid': s.st_uid,
            'mode': oct(stat.S_IMODE(s.st_mode)), 'readable': True,
            'process_has_exact_path': os.environ.get('GRB_LICENSE_FILE') == str(p),
            'pid': os.getpid(), 'epoch': time.time(), 'secret_contents_read_by_binding': False}


def safe_error_category(raw):
    """Return fixed categories only; raw vendor text may contain secret values."""
    value = raw.decode('utf8', 'replace').lower() if raw else ''
    patterns = (
        ('license file', 'LICENSE_FILE_CONFIGURATION'), ('no license', 'NO_LICENSE'),
        ('expired', 'EXPIRED'), ('not valid', 'NOT_VALID'), ('unauthorized', 'UNAUTHORIZED'),
        ('invalid', 'INVALID'), ('token', 'TOKEN_SERVICE'), ('wls', 'WLS_SERVICE'),
        ('resolve', 'DNS_RESOLUTION'), ('connect', 'CONNECTION'), ('network', 'NETWORK'),
        ('certificate', 'TLS_CERTIFICATE'), ('ssl', 'TLS'), ('permission', 'PERMISSION'),
        ('hostid', 'HOST_ID'), ('size', 'SIZE_LIMIT'), ('version', 'VERSION'),
    )
    return [category for text, category in patterns if text in value] or ['UNCLASSIFIED_NATIVE_LICENSE_ERROR']


def start_environment(lib, env, record):
    """Exactly one real start call, with credential-free diagnostics before freeenv."""
    metadata = bind_license()
    started = time.monotonic()
    code = int(lib.GRBstartenv(env))
    receipt = dict(metadata, native_call='GRBstartenv', native_return_code=code,
                   native_environment_started=(code == 0), seconds=time.monotonic()-started,
                   raw_native_error_persisted=False, retry=False)
    if code:
        try:
            lib.GRBgeterrormsg.argtypes = [C.c_void_p]
            lib.GRBgeterrormsg.restype = C.c_char_p
            receipt['sanitized_native_error_categories'] = safe_error_category(lib.GRBgeterrormsg(env))
        except Exception:
            receipt['sanitized_native_error_categories'] = ['DIAGNOSTIC_UNAVAILABLE']
    record(receipt)
    return code
