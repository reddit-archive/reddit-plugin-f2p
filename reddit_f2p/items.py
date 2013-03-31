import random
import re

from pylons import g

from reddit_f2p import inventory, effects, scores, gamelog

from r2.models import Account, Comment, Link
from r2.models.admintools import send_system_message


ITEMS = {}


def title_to_camel(name):
    # http://stackoverflow.com/a/1176023/9617
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_item(item_name):
    item_cls = ITEMS.get(item_name, Item)
    return item_cls(item_name)


def registered_item(cls):
    item_name = title_to_camel(cls.__name__)
    ITEMS[item_name] = cls
    return cls


TARGET_DISCRIMINATORS = {
    "account": lambda t: isinstance(t, Account),
    "usertext": lambda t: (isinstance(t, Comment) or
                           (isinstance(t, Link) and t.is_self)),
    "link": lambda t: isinstance(t, Link),
}


class Item(object):
    def __init__(self, item_name):
        self.item_name = item_name
        self.item = g.f2pitems[self.item_name]

    def is_target_valid(self, target):
        target_types = self.item["targets"]
        for target_type in target_types:
            discriminator = TARGET_DISCRIMINATORS.get(target_type)
            if not discriminator:
                g.log.debug("don't know how to validate target type %s",
                            target_type)
                continue

            if discriminator(target):
                return True
        return False

    def on_drop(self, user):
        inventory.add_to_inventory(user, self.item_name)

    def on_use(self, user, target):
        effects.add_effect(user, target, self.item_name)
        self.apply_damage_and_log(user, target, [target])

    def apply_damage_and_log(self, user, target, affected_things):
        damage = self.item["damage"]
        if damage:
            points = scores.apply_damage(affected_things, damage)
        else:
            points = {}

        gamelog.GameLogEntry.create(
            user._fullname,
            target._fullname,
            self.item_name,
            points,
        )

    def on_reply(self, user, parent):
        pass


@registered_item
class Abstinence(Item):
    def on_drop(self, user):
        effects.add_effect(user, user, self.item_name)
        super(Abstinence, self).on_drop(user)

    def on_use(self, user, target):
        effects.remove_effect(user, self.item_name)
        inventory.add_to_inventory(target, self.item_name)
        super(Abstinence, self).on_use(user, target)


class HealingItem(Item):
    def on_use(self, user, target):
        all_effects = effects.get_all_effects([target._fullname])
        target_effects = all_effects.get(target._fullname, [])
        target_afflictions = [e for e in target_effects
                              if not e.endswith("_hat")]

        if target_afflictions:
            to_heal = random.choice(target_afflictions)
            effects.remove_effect(target, to_heal)
            to_heal_title = g.f2pitems[to_heal]['title']
            item_title = self.item['title']
            msg = '%s used %s to heal of %s' % (user.name, item_title,
                                                to_heal_title)
        else:
            item_title = self.item['title']
            msg = ('%s used %s to heal you but you were '
                   'fully healthy. what a waste' % (user.name, item_title))
        subject = 'you have been healed!'

        if isinstance(target, Account):
            send_system_message(target, subject, msg)

        self.apply_damage_and_log(user, target, [target])


@registered_item
class Panacea(HealingItem):
    pass


@registered_item
class Melodies(HealingItem):
    pass


@registered_item
class Capitulation(Item):
    def on_use(self, user, target):
        subject = 'you have been poked!'
        item_title = self.item['title']
        msg = 'you were poked by %s (with %s)' % (user.name, item_title)
        send_system_message(target, subject, msg)
        self.apply_damage_and_log(user, target, [target])


@registered_item
class Overpowered(Item):
    def on_use(self, user, target):
        effects.clear_effects(target)
        inventory.clear_inventory(target)
        item_title = self.item['title']
        subject = 'you were assassinated!'
        msg = ('you were assassinated by %s (with %s) and lost all your items'
               ' and effects' % (user.name, item_title))
        send_system_message(target, subject, msg)

        self.apply_damage_and_log(user, target, [target])


@registered_item
class Magnet(Item):
    def on_use(self, user, target):
        target_items = [item_dict['kind']
                        for item_dict in inventory.get_inventory(target)]
        if target_items:
            to_steal = random.choice(target_items)
            inventory.consume_item(target, to_steal)
            inventory.add_to_inventory(user, to_steal)

            to_steal_title = g.f2pitems[to_steal]['title']
            item_title = self.item['title']
            subject = "you've been robbed!"
            msg = ('%s used %s to steal your %s' %
                   (user.name, item_title, to_steal_title))
            send_system_message(target, subject, msg)

            subject = "you stole an item"
            msg = ("you used %s to steal %s from %s" %
                   (item_title, to_steal_title, target.name))
            send_system_message(user, subject, msg)

            self.apply_damage_and_log(user, target, [target])


@registered_item
class Wand(Item):
    def on_use(self, user, target):
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
        target_random_item_name = random.choice(target_items)
        target_random_item = get_item(target_random_item_name)
        target_random_item.on_use(user, target)

        if random.random() > 0.5:
            user_items = [item_dict['kind'] for item_dict in g.f2pitems.values()
                          if (item_dict['targets'] and
                              'account' in item_dict['targets'])]
            user_random_item_name = random.choice(user_items)
            user_random_item = get_item(user_random_item_name)
            user_random_item.on_use(user, user)
        # TODO: messages?


class Trap(Item):
    def on_use(self, user, target):
        effects.add_effect(user, target, self.item_name)

    def on_reply(self, user, target):
        effector = effects.get_effector(self.item_name, target._fullname)
        effects.remove_effect(target, self.item_name)
        self.apply_damage_and_log(effector, target, [user])


@registered_item
class Caltrops(Trap):
    pass


@registered_item
class Propinquity(Trap):
    pass
