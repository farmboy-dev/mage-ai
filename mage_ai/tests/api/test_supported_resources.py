from unittest.mock import patch

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from mage_ai.server.api.base import BaseApiHandler
from mage_ai.server.api.v1 import ApiResourceListHandler
from mage_ai.api.operations.base import BaseOperation


class ProbeHandler(BaseApiHandler):
    def get(self, **kwargs):
        self.write({'ok': True})


class SupportedResourceTest(AsyncHTTPTestCase):
    def get_app(self):
        return Application([
            (r'/protected/(?P<resource>\w+)', ApiResourceListHandler),
            (r'/api/(?P<resource>\w+)(?:/(?P<pk>\w+))?(?:/(?P<child>\w+))?', ProbeHandler),
        ])

    def test_unknown_resource_methods_and_parent_child_are_404(self):
        with patch('mage_ai.api.middleware.REQUIRE_USER_AUTHENTICATION', False):
            for name in ['clusters', 'compute_clusters', 'compute_connections',
                         'compute_services', 'unregistered_resources']:
                for path in [f'/api/{name}', f'/api/{name}/id',
                             f'/api/{name}/id/blocks', f'/api/pipelines/id/{name}']:
                    for method in ['GET', 'POST', 'PUT', 'DELETE']:
                        response = self.fetch(path, method=method,
                                              body='{}' if method in ('POST', 'PUT') else None)
                        self.assertEqual(response.code, 404, (path, method, response.body))

    def test_supported_resource_is_preserved(self):
        with patch('mage_ai.api.middleware.REQUIRE_USER_AUTHENTICATION', False):
            self.assertEqual(self.fetch('/api/pipelines').code, 200)

    def test_import_errors_inside_existing_resources_are_not_hidden(self):
        operation = BaseOperation(resource='pipelines')
        operation.validate_resource()
        with patch('importlib.import_module', side_effect=ImportError('dependency failure')):
            with self.assertRaisesRegex(ImportError, 'dependency failure'):
                operation._BaseOperation__resource_class()

    def test_supported_resource_keeps_authentication(self):
        with patch('mage_ai.api.middleware.REQUIRE_USER_AUTHENTICATION', True):
            response = self.fetch('/protected/pipelines')
            self.assertEqual(response.code, 401)
