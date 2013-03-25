from pylons import g


TEAMS = {
    "blue": "deep blue",
    "red": "redzone",
}


def get_scoreboard():
    scores = g.f2pcache.get_multi(TEAMS.keys(), prefix="score_")

    scoreboard = {}
    for team, team_title in TEAMS.iteritems():
        scoreboard[team + "_title"] = team_title
        scoreboard[team + "_score"] = scores.get(team, 0)
    return scoreboard
