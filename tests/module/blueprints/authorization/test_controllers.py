import unittest

import jwt
from collections import namedtuple

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch
from importlib import import_module
module = import_module('conductor.blueprints.authorization.controllers')


class AuthorizationTest(unittest.TestCase):

    # Actions

    def setUp(self):

        # Cleanup
        self.addCleanup(patch.stopall)

        goog_provider = namedtuple("resp",['headers'])({'Location':'google'})
        oauth_response = {
            'access_token': 'access_token'
        }
        module.google_remote_app = Mock(
            return_value=namedtuple('google_remote_app',
                                    ['authorize', 'authorized_response'])
            (authorize=lambda **kwargs:goog_provider,
             authorized_response=lambda **kwargs:oauth_response)
        )

    # Tests

    def test___check___no_token(self):
        ret = module.Check()(None, 'service')
        self.assertEquals(len(ret.get('permissions')), 0)

    def test___check___no_service(self):
        ret = module.Check()('token', 'service')
        self.assertEquals(len(ret.get('permissions')), 0)

    def test___check___bad_token(self):
        ret = module.Check()('token', 'service')
        self.assertEquals(len(ret.get('permissions')), 0)

    def test___check___good_token(self):
        token = {
            'userid': 'userid',
        }
        client_token = jwt.encode(token, module.PRIVATE_KEY)
        ret = module.Check()(client_token, 'os.datastore')
        self.assertEquals(ret.get('service'), 'os.datastore')
        self.assertGreater(len(ret.get('permissions',{})), 0)
