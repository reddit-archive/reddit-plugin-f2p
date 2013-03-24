import json
import random

from pylons import g, c

from r2.lib.hooks import HookRegistrar
from r2.lib.utils import weighted_lottery
from r2.models import Account, Comment


hooks = HookRegistrar()
VALID_TARGETS = (Account, Comment)


def is_eligible_request():
    """Return whether or not the request is eligible to drop items."""
    return True  # TODO


def add_to_inventory(user, item):
    """Add a given item-name to the user's inventory."""
    inventory_key = "inventory_%d" % user._id
    with g.make_lock("f2p_inventory", "f2p_inventory_%d" % user._id):
        inventory_data = g.f2pcache.get(inventory_key, default="{}")
        inventory = json.loads(inventory_data)
        inventory[item] = inventory.get(item, 0) + 1
        g.f2pcache.set(inventory_key, json.dumps(inventory))


def get_inventory(user):
    inventory_data = g.f2pcache.get("inventory_%d" % user._id, default="{}")
    inventory = json.loads(inventory_data)

    inventory_view = []
    for kind, count in inventory.iteritems():
        for i in xrange(count):
            item = {"kind": kind}
            item.update(g.f2pitems[kind])
            inventory_view.append(item)
    return inventory_view


def drop_item():
    """Choose an item and add it to the user's inventory."""

    weights = dict.fromkeys(g.f2pitems.keys(), 100)
    weights.update(g.live_config["f2p_item_weights"])
    item_name = weighted_lottery(weights)

    g.log.debug("dropping item %r for %r", item_name, c.user.name)
    c.js_preload.add("#drop", [item_name])
    add_to_inventory(c.user, item_name)


def check_for_drops():
    """Determine if it is time to give the user a new item and do so."""
    if not c.user_is_loggedin:
        return

    if not is_eligible_request():
        return

    # if we do get a drop, how long should we wait 'til the next one?
    mu = g.live_config["drop_cooldown_mu"]
    sigma = g.live_config["drop_cooldown_sigma"]
    next_cooldown = max(1, int(random.normalvariate(mu, sigma)))

    # alright, let's see if the user's gonna get an item
    should_drop = g.f2pcache.add("drop_cooldown_%d" % c.user._id, "",
                                 time=next_cooldown)
    if should_drop:
        drop_item()


@hooks.on("reddit.request.begin")
def on_request():
    check_for_drops()

    c.js_preload.add("#inventory", get_inventory(c.user))
    c.js_preload.add("#game_status", {
        "blue_score": 4354,
        "blue_title": "deep blue",
        "red_score": 8204,
        "red_title": "redzone",
    })


@hooks.on("add_props")
def find_effects(items):
    things = [item for item in items
              if isinstance(item.lookups[0], VALID_TARGETS)]

    if not things:
        return

    fullnames = set()
    fullnames.update(item._fullname for item in things)
    fullnames.update(item.author._fullname for item in things)

    effects = g.f2pcache.get_multi(fullnames, prefix="effect_")
    g.log.debug("effects = %r", effects)

    # TODO: add effects to js_preload
