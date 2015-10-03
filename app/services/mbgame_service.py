import os
import requests
import logging
import pytz
from dateutil import parser
from datetime import timedelta, datetime


logger = logging.getLogger(__name__)


class MBGameService(object):
    SERVER_URL = 'http://localhost:3000/api/v1'
    AI_PLAYER_EMAIL = 'mbbot@dev.com'

    auth_token = None
    auth_token_expiration = None

    def __init__(self, email=None, password=None):
        self.email = email or self.AI_PLAYER_EMAIL
        self.password = password or os.getenv('AI_PLAYER_PASSWORD')
        self._authenticate()

    def get_active_games(self):
        self._validate_auth()

        params = {
            'status': 'active',
            'is_active_player': True
        }

        response = requests.get(
            url='{}/games'.format(self.SERVER_URL),
            params=params,
            headers=self._get_headers()
        )

        response_data = response.json()

        if response.status_code != 200:
            logger.warning('Auth failed: {}'.format(response_data))

        return response_data

    def make_move(self, game_id, pile, beans):
        self._validate_auth()

        data = {
            'game': {
                'pile': pile,
                'beans': beans
            }
        }

        response = requests.patch(
            url='{}/games/{}'.format(self.SERVER_URL, game_id),
            json=data,
            headers=self._get_headers()
        )

        response_data = response.json()

        if response.status_code != 200:
            logger.warning('Failed to update game {}: {}'.format(game_id, response_data))

    def _get_headers(self):
        return {'Authorization': 'Token token={}'.format(self.auth_token)}

    def _authenticate(self):
        data = {
          'user': {
            'email': self.email,
            'password': self.password
          }
        }

        response = requests.post(
            url='{}/users/auth'.format(self.SERVER_URL),
            json=data
        )

        response_data = response.json()

        if response.status_code != 200:
            logger.warn('Auth failed: {}'.format(response_data))

        self.auth_token = response_data['api_token']
        self.auth_token_expiration = parser.parse(response_data['api_token_expiration'])

    def _validate_auth(self):
        if (self.auth_token_expiration - timedelta(seconds=2)) < datetime.utcnow().replace(tzinfo=pytz.UTC):
            self._authenticate()