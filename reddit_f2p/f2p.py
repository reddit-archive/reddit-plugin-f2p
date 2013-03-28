import random
from uuid import UUID

from pylons import g, c, request

from r2.controllers import add_controller
from r2.controllers.reddit_base import RedditController
from r2.lib.base import abort
from r2.lib.db.thing import Thing
from r2.lib.errors import errors
from r2.lib.hooks import HookRegistrar
from r2.lib.pages import Reddit
from r2.lib.utils import weighted_lottery
from r2.lib.validator import (
    nop,
    validate,
    VLimit,
    VRequired,
    VByName,
)
from r2.lib.wrapped import Wrapped
from r2.models import (
    Account,
    Comment,
    Link,
    QueryBuilder,
    Subreddit,
    TableListing,
)
from reddit_f2p import procs, inventory, effects, scores, gamelog


hooks = HookRegistrar()
VALID_TARGETS = (Account, Comment)


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
                               if i["rarity"] == item_class])

    g.log.debug("dropping item %r for %r", item_name, c.user.name)
    proc = procs.get_item_proc("drop", item_name)
    proc(c.user, item_name)
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

    user_effects = effects.get_effects([c.user._fullname])
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


@hooks.on("comment.gild")
def gild_comment_effect(comment, gilder):
    """Add an effect to the gilded comment author."""
    author = Account._byID(comment.author_id, data=True)
    g.log.debug('%s got gilded, give them an effect!' % author.name)
    pass


@hooks.on("comment.new")
def comment_reply_effect(comment):
    parent_id = (comment.parent_id if hasattr(comment, 'parent_id')
                 else comment.link_id)
    parent = Thing._byID(parent_id)
    parent_effects = effects.get_effects([parent._fullname])
    reply_effects = []
    if reply_effects:
        pass


@add_controller
class FreeToPlayApiController(RedditController):
    @validate(item=VRequired('item', errors.NO_NAME),
              target=VByName('target'))
    def POST_use_item(self, item, target):
        try:
            inventory.consume_item(c.user, item)
        except inventory.NoSuchItemError:
            abort(400)

        proc = procs.get_item_proc("use", item)
        proc(c.user, target, item)


@add_controller
class GameLogController(RedditController):
    @validate(num=VLimit('limit', default=100, max_limit=500),
              after=nop('after'),
              before=nop('before'))
    def GET_listing(self, num, after, before):
        if before:
            after = before
            reverse = True
        else:
            reverse = False

        q = gamelog.GameLog.query(reverse=reverse, num=num)

        def after_fn(item):
            if isinstance(item, basestring):
                name, id = item.split('_')
                q.column_start = UUID(id)
            elif isinstance(item, gamelog.GameLogEntry):
                q.column_start = item._id
        q._after = after_fn

        if after:
            q._after(after)

        builder = QueryBuilder(q, skip=False, num=num, reverse=reverse)

        def wrap_items_fn(items):
            wrapped = []
            for item in items:
                w = Wrapped(item)
                wrapped.append(w)
            gamelog.GameLogEntry.add_props(c.user, wrapped)
            return wrapped

        builder.wrap_items = wrap_items_fn
        listing = TableListing(builder)
        return Reddit(content=listing.listing(),
                      extension_handling=False).render()
