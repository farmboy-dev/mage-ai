import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from mage_ai.data_preparation.executors.executor_factory import ExecutorFactory



class CloudExecutionRemovedTest(unittest.IsolatedAsyncioTestCase):
    def pipeline(self, executor='local_python', pipeline_type='python'):
        block = Mock(type='transformer', content='spark.range(1)')
        block.get_executor_type.return_value = executor
        pipeline = Mock(type=pipeline_type)
        pipeline.get_executor_type.return_value = executor
        pipeline.get_block.return_value = block
        return pipeline

    def test_removed_executor_rejected_at_every_dispatch_entry(self):
        for value in ['unknown_executor']:
            with self.subTest(executor=value):
                pipeline = self.pipeline(value)
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    ExecutorFactory.get_pipeline_executor(pipeline)
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    ExecutorFactory.get_block_executor(pipeline, 'block')
                with patch.dict(os.environ, DEFAULT_EXECUTOR_TYPE=value):
                    with self.assertRaisesRegex(ValueError, 'Unsupported'):
                        ExecutorFactory.get_pipeline_executor(self.pipeline())
                    with self.assertRaisesRegex(ValueError, 'Unsupported'):
                        ExecutorFactory.get_block_executor(self.pipeline(), 'block')
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    ExecutorFactory.get_pipeline_executor(self.pipeline(), executor_type=value)
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    ExecutorFactory.get_block_executor(self.pipeline(), 'block', executor_type=value)

    def test_pyspark_pipeline_uses_configured_execution_infrastructure(self):
        pipeline = self.pipeline(pipeline_type='pyspark')
        with patch('mage_ai.data_preparation.executors.executor_factory.PipelineExecutor') as p, \
                patch('mage_ai.data_preparation.executors.executor_factory.BlockExecutor') as b:
            self.assertIs(ExecutorFactory.get_pipeline_executor(pipeline), p.return_value)
            self.assertIs(ExecutorFactory.get_block_executor(pipeline, 'block'), b.return_value)
        pipeline.get_executor_type.return_value = 'k8s'
        self.assertEqual(ExecutorFactory.get_pipeline_executor_type(pipeline), 'k8s')

    def test_local_and_kubernetes_dispatch_are_preserved(self):
        for value, pipeline_target, block_target in [
            ('local_python', 'mage_ai.data_preparation.executors.executor_factory.PipelineExecutor',
             'mage_ai.data_preparation.executors.executor_factory.BlockExecutor'),
            ('k8s', 'mage_ai.data_preparation.executors.k8s_pipeline_executor.K8sPipelineExecutor',
             'mage_ai.data_preparation.executors.k8s_block_executor.K8sBlockExecutor'),
        ]:
            with patch(pipeline_target) as p, patch(block_target) as b:
                pipeline = self.pipeline(value)
                self.assertIs(ExecutorFactory.get_pipeline_executor(pipeline, executor_type=value), p.return_value)
                self.assertIs(ExecutorFactory.get_block_executor(pipeline, 'block', executor_type=value), b.return_value)
                p.assert_called_once()
                b.assert_called_once()

    async def test_api_writes_reject_cloud_before_persistence(self):
        from mage_ai.api.resources.BlockResource import BlockResource
        from mage_ai.api.resources.PipelineResource import PipelineResource
        for resource in [BlockResource, PipelineResource]:
            for value in ['unknown_executor']:
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    await resource.create({'executor_type': value}, None)
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    await resource.update(None, {'executor_type': value})

    def test_old_cloud_config_is_readable_but_not_exposed_or_writable(self):
        from mage_ai.data_preparation.repo_manager import RepoConfig
        with tempfile.TemporaryDirectory() as path:
            Path(path, 'metadata.yaml').write_text('unknown_setting:\n  master_instance_type: old\nspark_config:\n  spark_master: local\n')
            config = RepoConfig(repo_path=path)
            self.assertEqual(config.spark_config['spark_master'], 'local')
            self.assertFalse({'unknown_setting'}.intersection(config.to_dict()))
            for key in {'unknown_setting'}:
                with self.assertRaisesRegex(ValueError, 'Unsupported'):
                    config.save(**{key: {}})

    def test_internal_spark_configuration_reaches_session_builder(self):
        # No Spark runtime is installed in the dev image; verify Mage's forwarding boundary.
        from mage_ai.data_preparation.models.block import Block
        block = SimpleNamespace(spark_init=False, spark=None, global_vars={},
                                pipeline=SimpleNamespace(type="python", spark_config={
                                    'spark_master': 'spark://internal-spark:7077',
                                    'app_name': 'internal',
                                    'others': {'spark.sql.shuffle.partitions': '2'},
                                }))
        with patch('mage_ai.data_preparation.models.block.SPARK_ENABLED', True), \
                patch('mage_ai.data_preparation.models.block.get_spark_session') as builder:
            self.assertIs(Block.get_spark_session(block), builder.return_value)
            config = builder.call_args.args[0]
            self.assertEqual(config.spark_master, 'spark://internal-spark:7077')
            self.assertEqual(config.others['spark.sql.shuffle.partitions'], '2')

    def test_only_kubernetes_workspace_factory_is_supported(self):
        from mage_ai.cluster_manager.workspace.base import Workspace
        from mage_ai.cluster_manager.manage import get_instances
        for cluster in ['unknown_workspace']:
            with self.assertRaisesRegex(ValueError, 'Unsupported workspace'):
                Workspace.workspace_class_from_type(cluster)
            with self.assertRaisesRegex(ValueError, 'Unsupported workspace'):
                get_instances(cluster)

    def test_spark_master_environment_is_preserved(self):
        from mage_ai.services.spark import spark
        from mage_ai.services.spark.config import SparkConfig
        session = Mock()
        session.getActiveSession.return_value = None
        conf = Mock()
        with patch.dict(os.environ, SPARK_MASTER_HOST='spark://internal-master:7077'), \
                patch.object(spark, 'SPARK_ENABLED', True), \
                patch.object(spark, 'SparkSession', session, create=True), \
                patch.object(spark, 'SparkConf', return_value=conf, create=True):
            spark.get_spark_session(None)
            session.builder.master.assert_called_with('spark://internal-master:7077')
            spark.get_spark_session(SparkConfig())
            conf.setMaster.assert_called_with('spark://internal-master:7077')
            spark.get_spark_session(SparkConfig(spark_master='local'))
            conf.setMaster.assert_called_with('local')
