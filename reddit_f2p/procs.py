import random

from pylons import c, g

from reddit_f2p import inventory, effects, scores, gamelog

from r2.models import Account, Comment, Link
from r2.models.admintools import send_system_message


def get_item_proc(type, item):
    proc = globals().get(type + "_" + item, None)
    if not proc:
        proc = globals().get(type + "_default")
    return proc


def drop_cloak(user, item_name):
    pass


def drop_default(user, item_name):
    inventory.add_to_inventory(user, item_name)


def drop_abstinence(user, item_name):
    effects.add_effect(user, item_name)
    drop_default(user, item_name)


def log_and_score(user, target, item, points=1, damage=None):
    scores.incr_score(scores.get_user_team(user), damage or points)
    kw = {'damage': damage} if damage else {'points': points}
    gamelog.GameLogEntry.create(user._fullname, target._fullname, item, **kw)


def use_abstinence(user, target, item_name):
    effects.remove_effect(user, item_name)
    effects.add_effect(target, item_name)
    inventory.add_to_inventory(target, item_name)
    log_and_score(user, target, item_name, damage=1)


def use_default(user, target, item):
    # TODO: check the target is of a valid type
    effects.add_effect(target, item)
    log_and_score(user, target, item, points=1)


def _use_healing_item(user, target, item):
    effect_dict = effects.get_all_effects([target._fullname])
    target_afflictions = []
    if isinstance(effect_dict, dict) and target._fullname in effect_dict:
        target_afflictions = effect_dict[target._fullname]

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

    log_and_score(user, target, item, points=1)


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
    log_and_score(user, target, item, damage=damage)


def use_overpowered(user, target, item):
    effects.clear_effects(target)
    inventory.clear_inventory(target)
    item_title = g.f2pitems[item]['title']
    subject = 'you were assassinated!'
    msg = ('you were assassinated by %s (with %s) and lost all your items and'
           ' effects' % (user.name, item_title))
    send_system_message(target, subject, msg)
    log_and_score(user, target, item, damage=1)


def use_magnet(user, target, item):
    target_items = [item_dict['kind']
                    for item_dict in inventory.get_inventory(target)]
    if target_items:
        to_steal = random.choice(target_items)
        inventory.consume_item(target, to_steal)
        inventory.add_to_inventory(user, to_steal)

        to_steal_title = g.f2pitems[to_steal]['title']
        item_title = g.f2pitems[item]['title']
        subject = "you've been robbed!"
        msg = ('%s used %s to steal your %s' %
               (user.name, item_title, to_steal_title))
        send_system_message(target, subject, msg)

        subject = "you stole an item"
        msg = ("you used %s to steal %s from %s" %
               (item_title, to_steal_title, target.name))
        send_system_message(user, subject, msg)
        log_and_score(user, target, item, points=1)


def use_wand(user, target, item):
    if isinstance(target, Account):
        target_type = 'account'
    elif isinstance(target, Comment):
        target_type = 'usertext'
    elif isinstance(target, Link):
        target_type = 'link'
    else:
        return

    target_items = [item_dict['kind'] for item_dict in g.f2pitems.values()
                    if (item_dict['targets'] and
                        target_type in item_dict['targets'])]
    target_random_item = random.choice(target_items)
    proc = get_item_proc('use', target_random_item)
    proc(user, target, target_random_item)
    log_and_score(user, target, item, points=1)

    if random.random() > 0.5:
        user_items = [item_dict['kind'] for item_dict in g.f2pitems.values()
                      if (item_dict['targets'] and
                          'account' in item_dict['targets'])]
        user_random_item = random.choice(user_items)
        proc = get_item_proc('use', user_random_item)
        proc(user, user, user_random_item)
    # TODO: messages?

