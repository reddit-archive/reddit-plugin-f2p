from pylons import c

from reddit_f2p import inventory, effects


def get_item_proc(type, item):
    proc = globals().get(type + "_" + item, None)
    if not proc:
        proc = globals().get(type + "_default")
    return proc


def drop_cloak(user, item_name):
    pass


def drop_default(user, item_name):
    c.js_preload.set("#drop", [item_name])
    inventory.add_to_inventory(user, item_name)


def use_default(user, target, item):
    # TODO: check the target is of a valid type
    effects.add_effect(target, item)
