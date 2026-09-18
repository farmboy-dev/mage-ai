import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mage_ai.data_preparation.executors.streaming_pipeline_executor import StreamingPipelineExecutor
from mage_ai.data_preparation.models.constants import BlockLanguage
from mage_ai.streaming.sources.source_factory import SourceFactory
from mage_ai.streaming.sinks.sink_factory import SinkFactory


class RemovedCloudStreamingTest(unittest.TestCase):
    def test_factories_reject_before_import(self):
        with patch('boto3.client', side_effect=AssertionError('Unexpected client')):
            for provider in ['unknown_connector']:
                for factory in [SourceFactory.get_source, SinkFactory.get_sink]:
                    with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
                        factory({'connector_type': provider})

    def test_removed_sink_prevents_yaml_and_python_source_initialization(self):
        for language in [BlockLanguage.YAML, BlockLanguage.PYTHON]:
            executor = StreamingPipelineExecutor.__new__(StreamingPipelineExecutor)
            executor.source_block = SimpleNamespace(
                uuid='source', language=language, content='connector_type: kafka')
            executor.sink_blocks = [
                SimpleNamespace(uuid='valid', language=BlockLanguage.YAML,
                                content='connector_type: amazon_s3'),
                SimpleNamespace(uuid='removed', language=BlockLanguage.YAML,
                                content="connector_type: '{{ variables(\"sink\") }}'"),
            ]
            with patch.object(SourceFactory, 'get_source') as source, \
                    patch.object(SourceFactory, 'get_python_source') as python_source, \
                    patch.object(SinkFactory, 'get_sink') as sink:
                with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
                    executor._StreamingPipelineExecutor__execute_in_python(
                        global_vars={'sink': 'unknown_connector'})
                source.assert_not_called()
                python_source.assert_not_called()
                sink.assert_not_called()

    def test_removed_source_prevents_initialization(self):
        executor = StreamingPipelineExecutor.__new__(StreamingPipelineExecutor)
        executor.source_block = SimpleNamespace(
            uuid='source', language=BlockLanguage.YAML, content='connector_type: unknown_connector')
        executor.sink_blocks = []
        with patch.object(SourceFactory, 'get_source') as source:
            with self.assertRaisesRegex(ValueError, 'Unsupported connector'):
                executor._StreamingPipelineExecutor__execute_in_python()
            source.assert_not_called()

    def test_supported_yaml_stream_delivers_batch_and_interpolates_once(self):
        from unittest.mock import Mock
        from mage_ai.streaming.sources.base import SourceConsumeMethod
        from mage_ai.data_preparation.models.constants import BlockType

        sink_block = SimpleNamespace(uuid='sink', language=BlockLanguage.YAML,
                                     content='connector_type: amazon_s3',
                                     type=BlockType.DATA_EXPORTER, downstream_blocks=[])
        executor = StreamingPipelineExecutor.__new__(StreamingPipelineExecutor)
        executor.pipeline = SimpleNamespace(pipeline_variables_dir='/tmp/streaming-test')
        executor.source_block = SimpleNamespace(
            uuid='source', language=BlockLanguage.YAML, content='connector_type: kafka',
            downstream_blocks=[sink_block])
        executor.sink_blocks = [sink_block]
        source = Mock(consume_method=SourceConsumeMethod.BATCH_READ)
        source.batch_read.side_effect = lambda handler: handler([{'value': 1}])
        sink = Mock()
        with patch.object(SourceFactory, 'get_source', return_value=source), \
                patch.object(SinkFactory, 'get_sink', return_value=sink), \
                patch.object(executor, '_StreamingPipelineExecutor__interpolate_vars',
                             wraps=executor._StreamingPipelineExecutor__interpolate_vars) as render:
            executor._StreamingPipelineExecutor__execute_in_python()
        self.assertEqual(render.call_count, 2)
        sink.batch_write.assert_called_once_with([{'value': 1}])
