import datetime
import json
import random
from uuid import uuid1, UUID

from pycassa.system_manager import TIME_UUID_TYPE
from pylons import g, c, request

from r2.controllers import add_controller
from r2.controllers.reddit_base import RedditController
from r2.lib.base import abort
from r2.lib.db import tdb_cassandra
from r2.lib.db.thing import Thing
from r2.lib.filters import _force_unicode
from r2.lib.hooks import HookRegistrar
from r2.lib.pages import Reddit, WrappedUser
from r2.lib.utils import tup, weighted_lottery
from r2.lib.validator import (
    nop,
    validate,
    VLimit,
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
from reddit_f2p import procs, inventory, effects, scores


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
class FreeToPlayController(RedditController):
    # TODO: validators etc.
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

        q = GameLog.query(reverse=reverse, num=num)

        def after_fn(item):
            if isinstance(item, basestring):
                name, id = item.split('_')
                q.column_start = UUID(id)
            elif isinstance(item, GameLogEntry):
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
            GameLogEntry.add_props(c.user, wrapped)
            return wrapped

        builder.wrap_items = wrap_items_fn
        listing = TableListing(builder)
        return Reddit(content=listing.listing(),
                      extension_handling=False).render()


class GameLogEntry(object):
    def __init__(self, _id, user_fullname, target_fullname, item, date,
                 **extras):
        self._id = _id
        self.user_fullname = user_fullname
        self.target_fullname = target_fullname
        self.item = item
        self.date = date
        self.extras = extras

    @classmethod
    def add_props(cls, user, wrapped):
        TITLE_MAX_WIDTH = 50

        user_fullnames = {w.user_fullname for w in wrapped}
        target_fullnames = {w.target_fullname for w in wrapped}

        users = Account._by_fullname(user_fullnames, data=True,
                                     return_dict=True)
        targets = Thing._by_fullname(target_fullnames, data=True,
                                     return_dict=True)

        author_ids = {t.author_id for t in targets.itervalues()
                      if hasattr(t, 'author_id')}
        link_ids = {t.link_id for t in targets.itervalues()
                    if hasattr(t, 'link_id')}
        sr_ids = {t.sr_id for t in targets.itervalues() if hasattr(t, 'sr_id')}

        authors = Account._byID(author_ids, data=True, return_dict=True)
        links = Link._byID(link_ids, data=True, return_dict=True)
        subreddits = Subreddit._byID(sr_ids, data=True, return_dict=True)

        target_things = {}
        for fullname, target in targets.iteritems():
            if isinstance(target, (Comment, Link)):
                author = authors[target.author_id]
                link = (target if isinstance(target, Link)
                        else links[target.link_id])
                title = _force_unicode(link.title)
                if len(title) > TITLE_MAX_WIDTH:
                    short_title = title[:TITLE_MAX_WIDTH] + '...'
                else:
                    short_title = title

                if isinstance(target, Link):
                    pieces = ('link', short_title, 'by', author.name)
                    
                else:
                    pieces = ('comment by', author.name, 'on', short_title)
                text = ' '.join(pieces)
                if isinstance(target, Link):
                    path = target.make_permalink(subreddits[link.sr_id])
                else:
                    path = target.make_permalink(link, subreddits[link.sr_id])
                target_things[fullname] = (text, path, title)
            elif isinstance(target, Account):
                target_things[fullname] = WrappedUser(target)

        for w in wrapped:
            w.user = WrappedUser(users[w.user_fullname])
            w.target = target_things[w.target_fullname]
            try:
                w.item = g.f2pitems[w.item]['title']
            except KeyError:
                pass
            w.user_team = scores.get_user_team(users[w.user_fullname])
            w.text = ''
            if 'damage' in w.extras:
                damage = w.extras['damage']
                w.text = ('for %s point%s of damage' %
                          (damage, 's' if damage > 1 else ''))
            if isinstance(w.target, WrappedUser):
                target_user = targets[w.target.fullname]
            else:
                target_user = authors[targets[w.target_fullname].author_id]
            w.target_team = scores.get_user_team(target_user)

    @property
    def _fullname(self):
        return '%s_%s' % (self.__class__.__name__, self._id)

    @classmethod
    def create(cls, user_fullname, target_fullname, item, **extras):
        _id = uuid1()
        date = datetime.datetime.now(g.tz)
        obj = cls(_id, user_fullname, target_fullname, item, date, **extras)
        GameLog.add_object(obj)
        return obj

    @classmethod
    def date_to_tuple(cls, d):
        # Assumes date is UTC
        date_fields = ('year', 'month', 'day', 'hour', 'minute', 'second',
                       'microsecond')
        return tuple(getattr(d, f) for f in date_fields)

    @classmethod
    def date_from_tuple(cls, t):
        date = datetime.datetime(*t)
        date = date.replace(tzinfo=g.tz)
        return date

    def to_json(self):
        return json.dumps(self.extras.update({
            'user': self.user_fullname,
            'target': self.target_fullname,
            'item': self.item,
            'date': self.date_to_tuple(self.date),
        }))

    @classmethod
    def from_json(cls, _id, blob):
        attr_dict = json.loads(blob)
        user = attr_dict.pop('user')
        target = attr_dict.pop('target')
        item = attr_dict.pop('item')
        date = cls.date_from_tuple(attr_dict.pop('date'))
        obj = cls(_id, user, target, item, date, **attr_dict)
        return obj

    def __repr__(self):
        return '%s <%s>' % (self.__class__.__name__, self._id)


class GameLog(tdb_cassandra.View):
    _use_db = True
    _connection_pool = 'main'
    _compare_with = TIME_UUID_TYPE
    _read_consistency_level = tdb_cassandra.CL.ONE

    _ROWKEY = 'ALL'

    @classmethod
    def _byID(cls, column_names, return_dict=True, properties=None):
        column_names = tup(column_names)
        try:
            columns = cls._cf.get(cls._ROWKEY, column_names)
        except tdb_cassandra.NotFoundException:
            raise tdb_cassandra.NotFound
        objs = cls._column_to_obj(columns)

    @classmethod
    def query(cls, after=None, reverse=False, num=1000):
        rowkeys = [cls._ROWKEY]
        return super(cls, cls).query(rowkeys, after, reverse, num)

    @classmethod
    def _rowkey(cls, entry):
        return cls._ROWKEY

    @classmethod
    def _obj_to_column(cls, entries):
        entries = tup(entries)
        columns = []
        for entry in entries:
            column = {entry._id: entry.to_json()}
            columns.append(column)
        if len(columns) == 1:
            return columns[0]
        else:
            return columns

    @classmethod
    def _column_to_obj(cls, columns):
        columns = tup(columns)
        objs = []
        for column in columns:
            _id, blob = column.items()[0]
            objs.append(GameLogEntry.from_json(_id, blob))
        if len(objs) == 1:
            return objs[0]
        else:
            return objs
