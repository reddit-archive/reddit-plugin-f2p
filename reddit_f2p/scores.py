import collections

from pylons import g, c

from r2.lib.utils import tup
from r2.models import Account


TEAMS = {
    "blue": "periwinkle",
    "red": "orangered",
}


def get_user_team(user):
    return get_userid_team(user._id)


def get_userid_team(user_id):
    return "red" if user_id % 2 == 0 else "blue"


def get_opposite_team(team):
    return "red" if team == "blue" else "blue"


def get_game_status():
    scores = g.f2pcache.get_multi(TEAMS.keys(), prefix="score_")

    scoreboard = {}
    for team, team_title in TEAMS.iteritems():
        scoreboard[team + "_title"] = team_title
        scoreboard[team + "_score"] = scores.get(team, 0)

    if c.user_is_loggedin:
        scoreboard["user_team"] = get_user_team(c.user)

    return scoreboard


def incr_score(team, delta):
    assert team in TEAMS.keys()
    score_key = 'score_%s' % team
    g.f2pcache.add(score_key, 0)
    g.f2pcache.incr(score_key, delta=delta)
    c.state_changes["scores"][team] += delta


def _get_thing_userid(thing):
    try:
        return thing.author_id
    except AttributeError:
        assert isinstance(thing, Account)
        return thing._id


def apply_damage(things, delta):
    delta = int(delta)
    totals = collections.Counter()

    get_scoring_team = lambda uid: get_opposite_team(get_userid_team(uid))
    if delta < 0:
        get_scoring_team = get_userid_team
        delta = abs(delta)

    for thing in tup(things):
        uid = _get_thing_userid(thing)
        if not uid: continue
        team = get_scoring_team(uid)
        totals[team] += delta

    for team, delta in totals.iteritems():
        incr_score(team, delta)
    return totals
