import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mage_ai.services.spark.api.service import API
from mage_ai.services.spark.api.local import LocalAPI


class StandaloneSparkUITest(unittest.IsolatedAsyncioTestCase):
    async def test_uninstalled_spark_has_empty_monitoring_without_network(self):
        config = SimpleNamespace(spark_config=None)
        with patch('mage_ai.services.spark.api.base.get_spark_session', side_effect=ImportError), \
                patch('mage_ai.services.spark.models.applications.Application.get_applications_from_cache', return_value={}), \
                patch('socket.getaddrinfo', side_effect=AssertionError('Unexpected connection')):
            api = API.build(repo_config=config)
            self.assertIsInstance(api, LocalAPI)
            self.assertEqual(await api.applications(), [])
            self.assertEqual(await api.jobs(), [])
            self.assertEqual(await api.executors(), [])
            self.assertIsNotNone(await api.environment())

    async def test_internal_spark_configuration_and_ui_url_preserved(self):
        config = SimpleNamespace(spark_config={'spark_master': 'spark://internal:7077'})
        session = SimpleNamespace(sparkContext=SimpleNamespace(
            uiWebUrl='http://internal-driver:4040',
            getConf=lambda: SimpleNamespace(getAll=lambda: [('spark.app.id', 'test-app')]),
        ))
        with patch('mage_ai.services.spark.api.base.get_spark_session', return_value=session) as build:
            api = API.build(repo_config=config)
            self.assertEqual(build.call_args.args[0].spark_master, 'spark://internal:7077')
            self.assertEqual(api.endpoint(), 'http://internal-driver:4040/api/v1')
            self.assertEqual(api.application_id, 'test-app')

    async def test_executor_list_is_empty_without_an_application(self):
        from mage_ai.api.errors import ApiError
        from mage_ai.api.resources.SparkExecutorResource import SparkExecutorResource
        with patch('mage_ai.services.spark.api.base.get_spark_session', side_effect=ImportError), \
                patch('mage_ai.services.spark.models.applications.Application.get_applications_from_cache', return_value={}):
            api = API.build(repo_config=SimpleNamespace(spark_config=None))
            with patch.object(SparkExecutorResource, 'build_api', return_value=api), \
                    patch.object(SparkExecutorResource, 'build_result_set', side_effect=lambda models, *args, **kwargs: models):
                self.assertEqual(await SparkExecutorResource.collection({}, {}, None), [])
                with self.assertRaises(ApiError):
                    await SparkExecutorResource.get_application_id()
