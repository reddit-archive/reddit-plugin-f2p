from pylons import g, c


TEAMS = {
    "blue": "periwinkle",
    "red": "orangered",
}


def get_user_team(user):
    return get_userid_team(user._id)


def get_userid_team(user_id):
    return "red" if user_id % 2 == 0 else "blue"


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
