import json
import contextlib

from pylons import g


@contextlib.contextmanager
def mutate_key(key, type_=dict):
    """Context manager to atomically mutate an object stored in memcached.

    The context manager returns an object which can be mutated and will be
    stored back in memcached when the context ends.  A lock is held while
    mutation is going on, so be quick!

    If there is currently no object in memcached, `type_` is called to make
    a new one.

    """
    with g.make_lock("f2p", "f2p_%s" % key):
        raw_json = g.f2pcache.get(key)
        data = json.loads(raw_json) if raw_json else type_()
        yield data
        g.f2pcache.set(key, json.dumps(data))
