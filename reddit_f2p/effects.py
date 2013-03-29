import json

from pylons import g, c

from reddit_f2p import scores
from reddit_f2p.utils import mutate_key


def is_effect_visible(effector, effect_item):
    visibility = effect_item.get("visibility", "all")

    if visibility == "team":
        if c.user_is_loggedin:
            self_team = scores.get_user_team(c.user)
            effector_team = scores.get_userid_team(effector)
            return self_team == effector_team
        else:
            return False
    elif visibility == "self":
        return c.user_is_loggedin and effector == c.user._id
    else:
        return True


def add_effect(thing, effect):
    """Apply an effect to a thing."""
    with mutate_key("effect_%s" % thing._fullname, type_=list) as effects:
        effects.append((c.user._id, effect))


def get_all_effects(fullnames):
    """Return a dict of fullname -> [effects] for the given fullnames."""
    effects = g.f2pcache.get_multi(fullnames, prefix="effect_")
    for fullname, effect_json in effects.iteritems():
        thing_effects = json.loads(effect_json)
        effects[fullname] = [effect for effector, effect in thing_effects]
    return effects


def get_visible_effects(fullnames):
    """Return a dict of fullname -> [effects] for the given fullnames."""
    g.log.warning("visible effects")
    effects = g.f2pcache.get_multi(fullnames, prefix="effect_")
    for fullname, effect_json in effects.iteritems():
        thing_effects = json.loads(effect_json)

        filtered_effects = []
        for effector, effect in thing_effects:
            effect_item = g.f2pitems[effect]
            if is_effect_visible(effector, effect_item):
                filtered_effects.append(effect)
        effects[fullname] = filtered_effects
    return effects


def remove_effect(thing, effect):
    with mutate_key("effect_%s" % thing._fullname, type_=list) as effects:
        try:
            effects.remove(effect)
        except ValueError:
            pass


def get_my_effects(user):
    """Return full item descriptions for all effects on the user given."""
    effects = get_all_effects([user._fullname])
    effect_names = effects.get(user._fullname, [])
    return [g.f2pitems[name] for name in effect_names]


def clear_effects(thing):
    with mutate_key("effect_%s" % thing._fullname, type_=list) as effects:
        del effects[:]
