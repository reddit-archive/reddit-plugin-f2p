import json

from reddit_f2p.utils import mutate_key

from pylons import g


class NoSuchItemError(Exception):
    pass


def add_to_inventory(user, item):
    """Add a given item-name to the user's inventory."""
    with mutate_key("inventory_%d" % user._id, type_=dict) as inventory:
        inventory[item] = inventory.get(item, 0) + 1


def consume_item(user, item):
    """Consume an item in the user's inventory or die trying."""
    with mutate_key("inventory_%d" % user._id, type_=dict) as inventory:
        if item not in inventory:
            raise NoSuchItemError()

        inventory[item] -= 1
        assert inventory[item] >= 0
        if inventory[item] == 0:
            del inventory[item]


def get_inventory(user):
    inventory_data = g.f2pcache.get("inventory_%d" % user._id, default="{}")
    inventory = json.loads(inventory_data)

    inventory_view = []
    for kind, count in inventory.iteritems():
        for i in xrange(count):
            inventory_view.append(g.f2pitems[kind])
    return inventory_view


def clear_inventory(user):
    with mutate_key("inventory_%d" % user._id, type_=dict) as inventory:
        inventory = {}
