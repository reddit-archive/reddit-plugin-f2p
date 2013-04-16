import json
from time import sleep

from r2.models import *
from r2.lib.utils import fetch_things2, progress
from reddit_f2p.scores import get_user_team


def get_participated():
    users = {}

    q = Account._query(Account.c.f2p != "", sort=asc("_date"), data=True)
    for user in progress(fetch_things2(q)):
        users[user._fullname] = user.f2p

    return users


def give_trophies(users):
    for fullname in progress(users):
        user = Account._by_fullname(fullname)
        team = get_user_team(user)

        trophy = Award.give_if_needed(
            codename="f2p_orangered" if team == "red" else "f2p_periwinkle",
            user=user,
        )
        if trophy:
            trophy._commit()

        sleep(.25)


def save_participated(data_path):
    users = get_participated()
    with open(data_path, "w") as f:
        json.dump(users, f)


def trophy_participated(data_path):
    with open(data_path, "r") as f:
        give_trophies(json.load(f))
