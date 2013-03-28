import random

from pylons import c, g

from reddit_f2p import inventory, effects, scores

from r2.models import Account
from r2.models.admintools import send_system_message


def get_item_proc(type, item):
    proc = globals().get(type + "_" + item, None)
    if not proc:
        proc = globals().get(type + "_default")
    return proc


def drop_cloak(user, item_name):
    pass


def drop_default(user, item_name):
    c.js_preload.set("#drop", [item_name])
    inventory.add_to_inventory(user, item_name)


def drop_abstinence(user, item_name):
    effects.add_effect(user, item_name)
    drop_default(user, item_name)


def use_abstinence(user, target, item_name):
    effects.remove_effect(user, item_name)
    effects.add_effect(target, item_name)
    inventory.add_to_inventory(target, item_name)


def use_default(user, target, item):
    # TODO: check the target is of a valid type
    effects.add_effect(target, item)


def _use_healing_item(user, target, item):
    target_afflictions = effects.get_effects([target._fullname]).values()[0]
    if target_afflictions:
        to_heal = random.choice(target_afflictions)
        effects.remove_effect(target, to_heal)
        to_heal_title = g.f2pitems[to_heal]['title']
        item_title = g.f2pitems[item]['title']
        msg = '%s used %s to heal of %s' % (user.name, item_title,
                                            to_heal_title)
    else:
        item_title = g.f2pitems[item]['title']
        msg = ('%s used %s to heal you but you were fully healthy. what a waste'
                % (user.name, item_title))
    subject = 'you have been healed!'

    if isinstance(target, Account):
        send_system_message(target, subject, msg)


def use_panacea(user, target, item):
    _use_healing_item(user, target, item)


def use_melodies(user, target, item):
    _use_healing_item(user, target, item)


def use_capitulation(user, target, item):
    damage = 1
    subject = 'you have been poked!'
    item_title = g.f2pitems[item]['title']
    msg = 'you were poked by %s (with %s) for %s damage' % (user.name,
                                                            item_title, damage)
    send_system_message(target, subject, msg)
    scores.incr_score(scores.get_user_team(target), damage)

