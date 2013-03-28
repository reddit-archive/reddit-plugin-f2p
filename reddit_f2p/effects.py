import json

from pylons import g

from reddit_f2p.utils import mutate_key


def add_effect(thing, effect):
    """Apply an effect to a thing."""
    with mutate_key("effect_%s" % thing._fullname, type_=list) as effects:
        effects.append(effect)


def get_effects(fullnames):
    """Return a dict of fullname -> [effects] for the given fullnames."""
    effects = g.f2pcache.get_multi(fullnames, prefix="effect_")
    for fullname, effect_json in effects.iteritems():
        effects[fullname] = json.loads(effect_json)
    return effects


def remove_effect(thing, effect):
    with mutate_key("effect_%s" % thing._fullname, type_=list) as effects:
        try:
            effects.remove(effect)
        except ValueError:
            pass


def get_my_effects(user):
    """Return full item descriptions for all effects on the user given."""
    effects = get_effects([user._fullname])
    effect_names = effects.get(user._fullname, [])
    return [g.f2pitems[name] for name in effect_names]


def clear_effects(thing):
    with mutate_key("effect_%s" % thing._fullname, type_=list) as effects:
        effects = []
