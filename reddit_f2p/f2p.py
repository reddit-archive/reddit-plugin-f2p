import collections
import json
import random

from pylons import g, c, request

from r2.controllers import add_controller
from r2.controllers.reddit_base import RedditController
from r2.lib.base import abort
from r2.lib.errors import errors
from r2.lib.hooks import HookRegistrar
from r2.lib.utils import weighted_lottery
from r2.lib.validator import (
    validate,
    VLimit,
    VRequired,
    VByName,
)
from r2.models import (
    Account,
    Comment,
    Link,
    Subreddit,
)
from reddit_f2p import items, inventory, effects, scores


hooks = HookRegistrar()
VALID_TARGETS = (Account, Comment, Link)


def is_eligible_request():
    """Return whether or not the request is eligible to drop items."""
    if request.method != 'GET':
        return False

    if request.environ.get('render_style') != 'html':
        return False

    routes_dict = request.environ.get('pylons.routes_dict', {})
    controller = routes_dict.get('controller')
    action_name = routes_dict.get('action_name')
    if controller == 'front' and action_name == 'comments':
        return True
    elif (controller in ('hot', 'new', 'rising', 'browse', 'randomrising',
                         'comments') and
          action_name == 'listing'):
        return True
    else:
        return False


def drop_item():
    """Choose an item and add it to the user's inventory.

    The rarity class of the item to drop is chosen by weighted lottery
    according to the weights configured in live config. An item from within
    that rarity class is then chosen uniformly at random.

    """

    item_class = weighted_lottery(g.live_config["f2p_rarity_weights"])
    item_name = random.choice([i["kind"] for i in g.f2pitems.itervalues()
                               if i.get("rarity", "common") == item_class])

    g.log.debug("dropping item %r for %r", item_name, c.user.name)
    item = items.get_item(item_name)
    item.on_drop(c.user)
    c.js_preload.set("#drop", [item_name])


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


def check_for_banana():
    if not c.user_is_loggedin or not is_eligible_request():
        return False

    user_effects = effects.get_all_effects([c.user._fullname])
    return 'banana' in user_effects


@hooks.on("reddit.request.begin")
def on_request():
    if check_for_banana() and random.random() < 0.05:
        abort(503)

    check_for_drops()

    if c.user_is_loggedin:
        c.js_preload.set("#myeffects", effects.get_my_effects(c.user))
        c.js_preload.set("#inventory", inventory.get_inventory(c.user))
    c.js_preload.set("#game_status", scores.get_game_status())
    c.visible_effects = {}
    c.score_deltas = collections.Counter()


@hooks.on("add_props")
def find_effects(items):
    things = [item for item in items
              if isinstance(item.lookups[0], VALID_TARGETS)]

    fullnames = set()
    fullnames.update(item._fullname for item in things)
    fullnames.update(item.author._fullname for item in things)
    fullnames -= set(c.visible_effects)

    if fullnames:
        visible_effects = effects.get_visible_effects(fullnames)
        c.visible_effects.update(visible_effects)


@hooks.on("js_preload.use")
def coalesce_effects_for_preload(js_preload):
    if c.visible_effects:
        js_preload.set("#effects", c.visible_effects)


@hooks.on("comment.gild")
def gild_comment_effect(comment, gilder):
    """Add an effect to the gilded comment author."""
    author = Account._byID(comment.author_id, data=True)
    g.log.debug('%s got gilded, give them an effect!' % author.name)
    pass


@hooks.on("comment.new")
def comment_reply_effect(comment):
    if comment.parent_id is not None:
        parent = Comment._byID(comment.parent_id)
    else:
        parent = Link._byID(comment.link_id)
    parent_effects = effects.get_all_effects([parent._fullname])
    for item_name in parent_effects:
        item = items.get_item(item_name)
        item.on_reply(c.user, parent)


@add_controller
class FreeToPlayApiController(RedditController):
    @validate(item_name=VRequired('item', errors.NO_NAME),
              target=VByName('target'))
    def POST_use_item(self, item_name, target):
        try:
            inventory.consume_item(c.user, item_name)
        except inventory.NoSuchItemError:
            abort(400)

        item = items.get_item(item_name)
        if not item.is_target_valid(target):
            abort(400)
        item.on_use(c.user, target)

        return json.dumps({
            "score_deltas": dict(c.score_deltas),
        })
