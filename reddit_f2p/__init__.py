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

        ConfigValue.dict(str, str): [
            "team_subreddits",
        ],
    }

    js = {
        'reddit': Module('reddit.js',
            'lib/iso8601.js',
            'f2p/scrollupdater.js',
            'f2p/f2p.js',
            'f2p/utils.js',
            'f2p/items.js',
            TemplateFileSource('f2p/panel.html'),
            TemplateFileSource('f2p/item.html'),
            TemplateFileSource('f2p/item-bubble.html'),
            TemplateFileSource('f2p/scores.html'),
            TemplateFileSource('f2p/target-overlay.html'),
        )
    }

    live_config = {
        ConfigValue.float: [
            'drop_cooldown_mu',
            'drop_cooldown_sigma',
        ],

        ConfigValue.dict(str, int): [
            'f2p_rarity_weights',
        ],
    }

    def on_load(self, g):
        # TODO: use SelfEmptyingCache for localcache if we use this in jobs
        f2p_memcaches = CMemcache(g.f2pcaches, num_clients=g.num_mc_clients)
        g.f2pcache = MemcacheChain((
            LocalCache(),
            f2p_memcaches,
        ))
        g.cache_chains.update(f2p=g.f2pcache)

        compendium = pkg_resources.resource_stream(__name__,
                                                   "data/compendium.json")
        g.f2pitems = json.load(compendium)
        for kind, data in g.f2pitems.iteritems():
            data["kind"] = kind

    def add_routes(self, mc):
        mc('/f2p/gamelog', controller='gamelog', action='listing')
        mc('/api/f2p/:action', controller='freetoplayapi')
        mc('/f2p/steam/:action', controller='steam', action='start')

    def load_controllers(self):
        from r2.lib.pages import Reddit
        Reddit.extra_stylesheets.append('f2p.less')

        from reddit_f2p import f2p
        f2p.hooks.register_all()
        f2p.monkeypatch()

        from reddit_f2p.steam import SteamController
        from reddit_f2p.gamelog import GameLogController
