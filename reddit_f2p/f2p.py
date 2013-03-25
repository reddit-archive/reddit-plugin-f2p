import random

from pylons import g, c

from r2.controllers import add_controller
from r2.controllers.reddit_base import RedditController
from r2.lib.base import abort
from r2.lib.hooks import HookRegistrar
from r2.lib.utils import weighted_lottery
from r2.models import Account, Comment
from reddit_f2p import procs, inventory, effects


hooks = HookRegistrar()
VALID_TARGETS = (Account, Comment)


def is_eligible_request():
    """Return whether or not the request is eligible to drop items."""
    return True  # TODO


def drop_item():
    """Choose an item and add it to the user's inventory."""

    # TODO: change this system to take advantage of common/uncommon/rare/etc.
    weights = dict.fromkeys(g.f2pitems.keys(), 100)
    weights.update(g.live_config["f2p_item_weights"])
    item_name = weighted_lottery(weights)

    g.log.debug("dropping item %r for %r", item_name, c.user.name)
    proc = procs.get_item_proc("drop", item_name)
    proc(c.user, item_name)


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

    c.js_preload.set("#myeffects", effects.get_my_effects(c.user))
    c.js_preload.set("#inventory", inventory.get_inventory(c.user))

    # TODO: get the score from a real data source
    c.js_preload.set("#game_status", {
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

    # TODO: it's possible for this hook to run multiple times in the same
    # request. will multiple preloads for the same URL cause issues?
    c.js_preload.set("#effects", effects.get_effects(fullnames))


@add_controller
class FreeToPlayController(RedditController):
    # TODO: validators etc.
    def POST_use_item(self, item, target):
        try:
            inventory.consume_item(c.user, item)
        except inventory.NoSuchItemError:
            abort(400)

        proc = procs.get_item_proc("use", item)
        proc(c.user, target)
