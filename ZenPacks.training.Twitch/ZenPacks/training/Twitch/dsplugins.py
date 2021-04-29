"""Monitors current conditions using the Twitch API."""

# Logging
import logging
LOG = logging.getLogger('zen.Twitch')

# stdlib Imports
import json
import time
from datetime import datetime
from dateutil import parser

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )
from modeler.plugins.Twitch.ContextFactory import WebClientContextFactory

class Alerts(PythonDataSourcePlugin):

    """Twitch alerts data source plugin."""

    @classmethod
    def config_key(cls, datasource, context):
        return (
            context.device().id,
            datasource.getCycleTime(context),
            context.id,
            'twitch-alerts',
            )

    @classmethod
    def params(cls, datasource, context):
        return {
            'user_name': context.user_name,
            'game_name': context.game_name,
            }

    @inlineCallbacks
    def collect(self, config):
        data = self.new_data()

        for datasource in config.datasources:
            try:
                response = yield getPage(
                    'https://api.weather.gov/alerts/active?zone={query}'
                    .format(
                        query=datasource.params['county']))

                response = json.loads(response)
            except Exception:
                LOG.exception(
                    "%s: failed to get alerts data for %s",
                    config.id,
                    datasource.params['station_name'])
                continue

            for rawAlert in response.get('features'):
                alert = rawAlert['properties']
                severity = None
                expires = parser.parse(alert['expires'])
                if datetime.timetuple(expires) <= time.gmtime():
                    severity = 0
                elif alert['certainty'] == 'Likely':
                    severity = 4
                else:
                    severity = 3

                data['events'].append({
                    'device': config.id,
                    'component': datasource.component,
                    'severity': severity,
                    'eventKey': 'nws-alert-{}'.format(alert['event'].replace(' ', '')),
                    'eventClassKey': 'nws-alert',

                    'summary': alert['headline'],
                    'message': alert['description'],

                    'nws-sender': alert['senderName'],
                    'nws-date': alert['effective'],
                    'nws-expires': alert['expires'],
                    'nws-category': alert['category'],
                    'nws-instruction': alert['instruction'],
                    'nws-type': alert['event'],
                    })

        returnValue(data)