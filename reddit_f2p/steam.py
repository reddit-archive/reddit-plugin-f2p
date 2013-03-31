import re

import openid.consumer.consumer
from pylons import g, c, request
from pylons.controllers.util import redirect_to, abort

from r2.controllers import add_controller
from r2.controllers.reddit_base import RedditController
from r2.lib.wrapped import Templated
from r2.lib.validator import validate, VUser
from r2.lib.pages import Reddit
from r2.lib.template_helpers import add_sr


STEAM_AUTH_URL = "http://steamcommunity.com/openid"
STEAMID_EXTRACTOR = re.compile("steamcommunity.com/openid/id/(.*?)$")


class SteamStart(Templated):
    pass


class SteamStop(Templated):
    pass


@add_controller
class SteamController(RedditController):
    @staticmethod
    def make_post_login_url():
        return add_sr("/f2p/steam/postlogin")

    @validate(VUser())
    def GET_start(self):
        f2p_status = getattr(c.user, "f2p")

        if f2p_status == "participated":
            return Reddit(content=SteamStart()).render()
        elif f2p_status == "claimed":
            return Reddit(content=SteamStop()).render()
        else:
            # TODO: something nicer?
            abort(404)


    @validate(VUser())
    def POST_auth(self):
        if getattr(c.user, "f2p") != "participated":
            abort(403)

        session = {}
        consumer = openid.consumer.consumer.Consumer(session, store=None)
        auth_request = consumer.begin(STEAM_AUTH_URL)
        post_login_url = self.make_post_login_url()
        url = auth_request.redirectURL(realm="http://" + g.domain,
                                       return_to=post_login_url)
        g.f2pcache.set("steam_session_%d" % c.user._id, session)
        g.log.debug("started steam auth for %s", c.user.name)
        return redirect_to(url)

    @validate(VUser())
    def GET_postlogin(self):
        if getattr(c.user, "f2p") != "participated":
            abort(403)

        session = g.f2pcache.get("steam_session_%d" % c.user._id)
        if not session:
            abort(404)

        consumer = openid.consumer.consumer.Consumer(session, store=None)
        auth_response = consumer.complete(request.params, request.url)

        if auth_response.status == openid.consumer.consumer.CANCEL:
            return redirect_to("/f2p/steam")

        if auth_response.status != openid.consumer.consumer.SUCCESS:
            abort(404)

        steamid_match = STEAMID_EXTRACTOR.search(auth_response.identity_url)
        if not steamid_match:
            abort(404)

        steamid = steamid_match.group(1)
        g.log.warning("successful steam auth for %r", steamid)

        # TODO: insert into a claim queue or something?

        return Reddit(content=SteamStop()).render()
