import random

from pylons import g, c

from r2.lib.hooks import HookRegistrar
from r2.models import Account, Comment


hooks = HookRegistrar()
VALID_TARGETS = (Account, Comment)


def is_eligible_request():
    """Return whether or not the request is eligible to drop items."""
    return True  # TODO


def drop_item():
    """Choose an item and add it to the user's inventory."""
    pass


@hooks.on("reddit.request.begin")
def on_request():
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

    c.js_preload.add("#inventory", [
        {"kind": "cruise", "title": "Cruise Missile"},
        {"kind": "downtime_banana", "title": "Banana of Downtime"},
        {"kind": "smpl_cdgl", "title": "Smpl Cdgl"},
        {"kind": "caltrops", "title": "Spiny Caltrops of the Spineless"},
        {"kind": "chirality", "title": "Scimitar of Chirality"},
    ])

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
