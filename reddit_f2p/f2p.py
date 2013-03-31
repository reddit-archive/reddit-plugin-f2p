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
from r2.lib.wrapped import Templated
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
    g.stats.event_count("f2p.drop", item_name)
    item = items.get_item(item_name)
    item.on_drop(c.user)
    c.js_preload.set("#drop", [item_name])


def award_gold_tophat():
    if not c.user.gold:
        return

    all_effects = effects.get_all_effects([c.user._fullname])
    user_effects = all_effects.get(c.user._fullname, [])

    ITEM_NAME = "gold_top_hat"
    if ITEM_NAME not in user_effects:
        effects.add_effect(effector=c.user, thing=c.user, effect=ITEM_NAME)


def check_for_drops():
    """Determine if it is time to give the user a new item and do so."""
    if not c.user_is_loggedin:
        return

    if not is_eligible_request():
        return

    award_gold_tophat()

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

    all_effects = effects.get_all_effects([c.user._fullname])
    user_effects = all_effects.get(c.user._fullname, [])
    return 'banana' in user_effects


class Downtime(Templated):
    pass


@hooks.on("reddit.request.begin")
def on_request():
    if check_for_banana() and random.random() < 0.01:
        request.environ["usable_error_content"] = Downtime().render()
        abort(503)

    scoreboard = scores.get_game_status()
    c.js_preload.set("#game_status", scoreboard)

    c.visible_effects = {}
    c.state_changes = {
        "status": scoreboard,
        "inventory": collections.defaultdict(list),
        "effects": collections.defaultdict(lambda:
                                           collections.defaultdict(list)),
        "myeffects": collections.defaultdict(list),
    }

    check_for_drops()

    if c.user_is_loggedin:
        find_effects([c.user._fullname])
        c.js_preload.set("#myeffects", effects.get_my_effects(c.user))
        c.js_preload.set("#inventory", inventory.get_inventory(c.user))


@hooks.on("add_props")
def on_add_props(items):
    things = [item for item in items
              if isinstance(item.lookups[0], VALID_TARGETS)]

    fullnames = set()
    fullnames.update(item._fullname for item in things)
    fullnames.update(item.author._fullname for item in things)
    fullnames -= set(c.visible_effects)

    return find_effects(fullnames)


def find_effects(fullnames):
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
        parent = Comment._byID(comment.parent_id, data=True)
    else:
        parent = Link._byID(comment.link_id, data=True)
    all_effects = effects.get_all_effects([parent._fullname])
    parent_effects = all_effects.get(parent._fullname, [])
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

        c.user.f2p = "participated"
        c.user._commit()

        item = items.get_item(item_name)
        if not item.is_target_valid(target):
            abort(400)
        item.on_use(c.user, target)

        return json.dumps(c.state_changes)


def monkeypatch():
    orig_is_contributor = Subreddit.is_contributor
    def is_contributor_with_teams(sr, user):
        sr_team = g.team_subreddits.get(sr.name.lower())
        if sr_team:
            return sr_team == scores.get_user_team(c.user)
        return orig_is_contributor(sr, user)
    Subreddit.is_contributor = is_contributor_with_teams
