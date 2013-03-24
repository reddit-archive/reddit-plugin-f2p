import random

from pylons import g, c

from r2.lib.hooks import HookRegistrar


hooks = HookRegistrar()


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


@hooks.on("js_config")
def add_to_js_config(config):
    # TODO: if a game event has happened, throw it in here.
    pass
