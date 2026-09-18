from unittest.mock import patch

from mage_ai.streaming.sources.activemq import ActiveMQSource
from mage_ai.streaming.sources.kafka import KafkaSource
from mage_ai.streaming.sources.nats_js import NATSSource
from mage_ai.streaming.sources.rabbitmq import RabbitMQSource
from mage_ai.streaming.sources.source_factory import SourceFactory
from mage_ai.tests.base_test import TestCase


class SourceFactoryTests(TestCase):
    def test_get_source_nats(self):
        with patch.object(NATSSource,
                          '__init__',
                          return_value=None) as mock_init:
            config = dict(
                connector_type='nats',
            )
            source = SourceFactory.get_source(config)
            self.assertIsInstance(source, NATSSource)
            mock_init.assert_called_once_with(config)

    def test_get_source_kafka(self):
        with patch.object(KafkaSource,
                          '__init__',
                          return_value=None) as mock_init:
            config = dict(
                connector_type='kafka',
            )
            source = SourceFactory.get_source(config)
            self.assertIsInstance(source, KafkaSource)
            mock_init.assert_called_once_with(config)

    def test_get_source_rabbitmq(self):
        with patch.object(RabbitMQSource,
                          '__init__',
                          return_value=None) as mock_init:
            config = dict(
                connector_type='rabbitmq',
            )
            source = SourceFactory.get_source(config)
            self.assertIsInstance(source, RabbitMQSource)
            mock_init.assert_called_once_with(config)

    def test_get_source_activemq(self):
        with patch.object(ActiveMQSource,
                          '__init__',
                          return_value=None) as mock_init:
            config = dict(
                connector_type='activemq',
            )
            source = SourceFactory.get_source(config)
            self.assertIsInstance(source, ActiveMQSource)
            mock_init.assert_called_once_with(config)

    def test_unknown_connector(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
            SourceFactory.get_source({'connector_type': 'unknown_connector'})
