"""Models Twitch channels using the Twitch API."""

# stdlib Imports
import json
import urllib
import pdb
from ContextFactory import WebClientContextFactory

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.internet import reactor

# Zenoss Imports
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin


class Channels(PythonPlugin):
    """Twitch Channels modeler plugin."""

    relname = 'twitchChannels'
    modname = 'ZenPacks.training.Twitch.TwitchChannel'

    requiredProperties = ('zTwitchChannels', 'zAuthorizationToken', 'zClientID',)

    deviceProperties = PythonPlugin.deviceProperties + requiredProperties


    @inlineCallbacks
    def collect(self, device, log):
        self.contextfactory = WebClientContextFactory()
        self.agent = Agent(reactor, self.contextfactory)

        """Asynchronously collect data from device. Return a deferred."""
        log.info("%s: collecting data", device.id)

        channels = getattr(device, 'zTwitchChannels', None)
        auth_token = getattr(device, 'zAuthorizationToken', None)
        client_id = getattr(device, 'zClientID', None)

        headers = {'Client-ID': client_id, 'Authorization': ["Bearer " + auth_token]}

        if not channels:
            log.error("%s: No channels.", device.id)
            returnValue(None)

        responses = []

        for channel in channels:
            try:
                response = yield self.agent.request("GET", "https://api.twitch.tv/helix/streams?user_login="+channel, Headers(headers))
                response = yield readBody(response)
                responses.append(response)
            except Exception, e:
                log.error("%s: %s", device.id, e)
                returnValue(None)

        result = DeferredList(responses, consumeErrors=True)
        returnValue(result)

    @inlineCallbacks
    def process(self, device, results, log):
        rm = self.relMap()

        for result in results:
            data = json.loads(result)
            data = data['data'][0]
            id = self.prepId(data['user_id'])
            user_name = data['user_name']
            language = data['language']
            thumbnail_url = data['thumbnail_url']
            rm.append(self.objectMap({
                'id': id,
                'user_name': user_name,
                'language': language,
                'thumbnail_url': thumbnail_url,
            }))
            pass
        return rm



