import json
import re

import openid.consumer.consumer
from pylons import g, c, request
from pylons.controllers.util import redirect_to, abort

from r2.controllers import add_controller
from r2.controllers.reddit_base import RedditController
from r2.lib import amqp
from r2.lib.wrapped import Templated
from r2.lib.validator import validate, VUser
from r2.lib.pages import Reddit
from r2.lib.template_helpers import add_sr
from r2.models import Account

from reddit_f2p import scores


STEAM_AUTH_URL = "http://steamcommunity.com/openid"
STEAMID_EXTRACTOR = re.compile("steamcommunity.com/openid/id/(.*?)$")
GRANT_URL = "http://api.steampowered.com/ITFPromos_440/GrantItem/v0001/"
QNAME = "steam_q"


class SteamPage(Reddit):
    def __init__(self, content):
        Reddit.__init__(
            self,
            show_sidebar=False,
            content=content,
        )


class SteamStart(Templated):
    pass


class SteamStop(Templated):
    pass


class SteamInProgress(Templated):
    pass


class SteamSorry(Templated):
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
            return SteamPage(content=SteamStart()).render()
        elif f2p_status == "claiming":
            return SteamPage(content=SteamInProgress()).render()
        elif f2p_status == "claimed":
            return SteamPage(content=SteamStop()).render()
        return SteamPage(content=SteamSorry()).render()

    @validate(VUser())
    # TODO: vmodhash
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
            return redirect_to("/f2p/steam")

        session = g.f2pcache.get("steam_session_%d" % c.user._id)
        if not session:
            return redirect_to("/f2p/steam")

        consumer = openid.consumer.consumer.Consumer(session, store=None)
        auth_response = consumer.complete(request.params, request.url)

        if auth_response.status == openid.consumer.consumer.CANCEL:
            return redirect_to("/f2p/steam")

        if auth_response.status != openid.consumer.consumer.SUCCESS:
            return redirect_to("/f2p/steam")

        steamid_match = STEAMID_EXTRACTOR.search(auth_response.identity_url)
        if not steamid_match:
            return redirect_to("/f2p/steam")

        steamid = steamid_match.group(1)
        g.log.debug("successful steam auth for %r", steamid)

        with g.make_lock("f2p", "steam_claim_%d" % c.user._id):
            c.user._sync_latest()
            if c.user.f2p != "participated":
                return redirect_to("/f2p/steam")

            c.user.f2p = "claiming"
            c.user._commit()

        message = json.dumps({
            "user-id": c.user._id,
            "steam-id": steamid,
        })
        amqp.add_item(QNAME, message)

        return redirect_to("/f2p/steam")


def run_steam_q():
    import requests

    session = requests.Session()
    session.headers.update({
        "User-Agent": g.useragent,
    })

    @g.stats.amqp_processor(QNAME)
    def _claim_hat(msg):
        data = json.loads(msg.body)

        account = Account._byID(int(data["user-id"]), data=True)
        if account.f2p != "claiming":
            g.log.warning("%r attempted to claim twice!", account)
            return

        user_team = scores.get_user_team(account)
        promo_id = g.steam_promo_items[user_team]

        g.stats.event_count("f2p.claim_hat", "item_%s" % promo_id)

        response = session.post(GRANT_URL, data={
            "SteamID": data["steam-id"],
            "PromoID": promo_id,
            "key": g.steam_api_key,
            "format": "json",
        })

        response_data = response.json()
        if response_data["status"] != "1":
            g.log.warning("Steam Promo for %r -> %r failed: %s",
                          account, data["steam-id"],
                          response_data["statusDetail"])
            raise Exception

        account.f2p = "claimed"
        account._commit()
    amqp.consume_items(QNAME, _claim_hat, verbose=True)
