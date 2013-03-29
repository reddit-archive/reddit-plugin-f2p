import datetime
import json
from uuid import uuid1

from pycassa.system_manager import TIME_UUID_TYPE
from pylons import g

from r2.lib.db import tdb_cassandra
from r2.lib.filters import _force_unicode
from r2.lib.pages import WrappedUser
from r2.lib.utils import tup
from r2.models import Account, Thing, Subreddit, Link, Comment

from reddit_f2p import scores


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
            if isinstance(w.target, WrappedUser):
                target_user = targets[w.target.fullname]
            else:
                target_user = authors[targets[w.target_fullname].author_id]
            w.target_team = scores.get_user_team(target_user)

            w.text = ''
            if 'damage' in w.extras:
                damage = w.extras['damage']
                w.text = ('for %s point%s of damage' %
                          (damage, 's' if damage > 1 else ''))
            elif 'points' in w.extras:
                points = w.extras['points']
                w.text = ('(+%s point%s for the %s team' %
                          (points, 's' if points > 1 else '', w.user_team))

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
        d = self.extras
        d.update({
            'user': self.user_fullname,
            'target': self.target_fullname,
            'item': self.item,
            'date': self.date_to_tuple(self.date),
        })
        return json.dumps(d)

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
