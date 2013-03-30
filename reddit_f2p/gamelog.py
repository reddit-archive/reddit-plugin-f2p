import datetime
import json
from uuid import uuid1, UUID

from pycassa.system_manager import TIME_UUID_TYPE
from pylons import g, c

from r2.controllers import add_controller
from r2.controllers.reddit_base import RedditController
from r2.lib.db import tdb_cassandra
from r2.lib.pages import Reddit, WrappedUser, Templated
from r2.lib.utils import tup
from r2.lib.validator import nop, validate, VLimit
from r2.lib.wrapped import Wrapped
from r2.models import (
    Account,
    Comment,
    Link,
    QueryBuilder,
    Subreddit,
    TableListing,
    Thing,
)

from reddit_f2p import scores


class GameLogPage(Templated):
    def __init__(self, listing):
        self.listing = listing
        self.scores = scores.get_game_status()
        Templated.__init__(self)


class GameLogTarget(Templated):
    def __init__(self, target, permalink, author):
        self.text = "%s (%s)" % (target.__class__.__name__, author.name)
        self.url = permalink
        Templated.__init__(self)


class GameLogEntry(object):
    def __init__(self, _id, user_fullname, target_fullname, item, date, points):
        self._id = _id
        self.user_fullname = user_fullname
        self.target_fullname = target_fullname
        self.item = item
        self.date = date
        self.points = points

    @classmethod
    def add_props(cls, user, wrapped):
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
                if isinstance(target, Link):
                    path = target.make_permalink(subreddits[target.sr_id])
                else:
                    link = links[target.link_id]
                    path = target.make_permalink(link, subreddits[link.sr_id])
                target_things[fullname] = GameLogTarget(target, path, author)
            elif isinstance(target, Account):
                target_things[fullname] = WrappedUser(target)

        for w in wrapped:
            w.is_self = (c.user_is_loggedin and
                         w.user_fullname == c.user._fullname)
            w.user = WrappedUser(users[w.user_fullname])
            w.target = target_things[w.target_fullname]
            w.item = g.f2pitems[w.item]
            w.user_team = scores.get_user_team(users[w.user_fullname])
            if isinstance(w.target, WrappedUser):
                target_user = targets[w.target.fullname]
            else:
                target_user = authors[targets[w.target_fullname].author_id]
            w.target_team = scores.get_user_team(target_user)

    @property
    def _fullname(self):
        return '%s_%s' % (self.__class__.__name__, self._id)

    @classmethod
    def create(cls, user_fullname, target_fullname, item, points):
        _id = uuid1()
        date = datetime.datetime.now(g.tz)
        obj = cls(_id, user_fullname, target_fullname, item, date, points)
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
        return json.dumps({
            'user': self.user_fullname,
            'target': self.target_fullname,
            'item': self.item,
            'date': self.date_to_tuple(self.date),
            'points': dict(self.points),
        })

    @classmethod
    def from_json(cls, _id, blob):
        attr_dict = json.loads(blob)
        user = attr_dict.pop('user')
        target = attr_dict.pop('target')
        item = attr_dict.pop('item')
        date = cls.date_from_tuple(attr_dict.pop('date'))
        points = attr_dict.pop('points', {})
        obj = cls(_id, user, target, item, date, points)
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
        content = GameLogPage(listing.listing())
        return Reddit(content=content,
                      page_classes=["gamelog"],
                      show_sidebar=False,
                      extension_handling=False).render()
