from r2.lib.hooks import HookRegistrar
from r2.lib.plugin import Plugin

hooks = HookRegistrar()


@hooks.on("reddit-request.begin")
def on_request():
    # TODO: determine if this is an eligible request
    # TODO: check for user drop cooldown
    # TODO: if not cooling down, choose an item
    # TODO: add item to user's inventory
    pass


@hooks.on("js_config")
def add_to_js_config(config):
    # TODO: if a game event has happened, throw it in here.
    pass


class FreeToPlay(Plugin):
    pass
