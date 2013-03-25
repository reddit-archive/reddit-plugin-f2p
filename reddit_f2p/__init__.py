import json

import pkg_resources

from r2.lib.cache import CMemcache, MemcacheChain, LocalCache
from r2.lib.configparse import ConfigValue
from r2.lib.plugin import Plugin
from r2.lib.js import Module, TemplateFileSource


class FreeToPlay(Plugin):
    needs_static_build = True

    config = {
        ConfigValue.tuple: [
            "f2pcaches",
        ],
    }

    js = {
        'reddit': Module('reddit.js',
            'f2p/f2p.js',
            TemplateFileSource('f2p/panel.html'),
            TemplateFileSource('f2p/item.html'),
            TemplateFileSource('f2p/scores.html'),
        )
    }

    live_config = {
        ConfigValue.float: [
            'drop_cooldown_mu',
            'drop_cooldown_sigma',
        ],

        ConfigValue.dict(str, int): [
            'f2p_item_weights',
        ],
    }

    def on_load(self, g):
        # TODO: use SelfEmptyingCache for localcache if we use this in jobs
        f2p_memcaches = CMemcache(g.f2pcaches, num_clients=g.num_mc_clients)
        g.f2pcache = MemcacheChain((
            LocalCache(),
            f2p_memcaches,
        ))

        compendium = pkg_resources.resource_stream(__name__,
                                                   "data/compendium.json")
        g.f2pitems = json.load(compendium)

    def load_controllers(self):
        from r2.lib.pages import Reddit
        Reddit.extra_stylesheets.append('f2p.less')

        from reddit_f2p import f2p
        f2p.hooks.register_all()
