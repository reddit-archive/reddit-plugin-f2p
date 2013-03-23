from r2.lib.plugin import Plugin
from r2.lib.js import Module


class FreeToPlay(Plugin):
    needs_static_build = True

    js = {
        'reddit': Module('reddit.js',
            'f2p.js',
        )
    }

    def load_controllers(self):
        from reddit_f2p import f2p
        f2p.hooks.register_all()
