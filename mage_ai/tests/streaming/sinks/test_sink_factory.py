from mage_ai.streaming.sinks.opensearch import OpenSearchSink
from mage_ai.streaming.sinks.sink_factory import SinkFactory
from mage_ai.tests.base_test import TestCase
from unittest.mock import patch


class SinkFactoryTests(TestCase):
    def test_get_source_kafka(self):
        with patch.object(OpenSearchSink, '__init__', return_value=None) as mock_init:
            config = dict(
                connector_type='opensearch',
            )
            sink = SinkFactory.get_sink(config)
            self.assertIsInstance(sink, OpenSearchSink)
            mock_init.assert_called_once_with(config)

    def test_unknown_connector(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
            SinkFactory.get_sink({'connector_type': 'unknown_connector'})
