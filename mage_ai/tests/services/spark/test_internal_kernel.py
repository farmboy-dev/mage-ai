import ast
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from mage_ai.server.kernels import (
    InternalSparkKernelSpecManager, KernelName, PIPELINE_TO_KERNEL_NAME,
)
from mage_ai.server.utils.output_display import (
    add_execution_code, get_block_output_process_code, get_internal_spark_init_code,
)


class InternalPySparkKernelTest(unittest.TestCase):
    def test_kernel_spec_uses_ipython_not_sparkmagic(self):
        spec = InternalSparkKernelSpecManager().get_kernel_spec(KernelName.PYSPARK)
        self.assertIn('ipykernel_launcher', spec.argv)
        self.assertNotIn('sparkmagic', ' '.join(spec.argv))
        self.assertEqual(PIPELINE_TO_KERNEL_NAME['pyspark'], KernelName.PYSPARK)

    def test_notebook_code_has_no_livy_magics_or_remote_transfer(self):
        for block_type in ['data_loader', 'transformer', 'chart', 'sensor']:
            code = add_execution_code('p', 'b', 'print(1)', {}, '/tmp/project',
                                      block_type=block_type, kernel_name=KernelName.PYSPARK,
                                      pipeline_config={'type': 'pyspark'})
            self.assertNotIn('%%spark', code)
            self.assertNotIn('%%local', code)
            ast.parse(code)
            self.assertIsNone(get_block_output_process_code('p', 'b', '/tmp/project',
                              block_type=block_type, kernel_name=KernelName.PYSPARK))

    def test_notebook_spark_init_uses_internal_configuration(self):
        config = {'spark_master': 'spark://internal-spark:7077', 'app_name': "team's pipeline",
                  'others': {'spark.sql.shuffle.partitions': '2'}}
        code = get_internal_spark_init_code(config)
        with patch('mage_ai.services.spark.spark.get_spark_session') as build:
            namespace = {}
            exec(code, namespace)
            self.assertEqual(build.call_args.args[0].spark_master, config['spark_master'])
            self.assertEqual(build.call_args.args[0].app_name, config['app_name'])
            self.assertIs(namespace['spark'], build.return_value)

    def test_missing_runtime_is_explicit_for_pyspark_only(self):
        from mage_ai.data_preparation.models.block import Block
        block = SimpleNamespace(pipeline=SimpleNamespace(type='pyspark'))
        with patch('mage_ai.data_preparation.models.block.SPARK_ENABLED', False):
            with self.assertRaisesRegex(ImportError, 'PySpark and Java'):
                Block.get_spark_session(block, raise_errors=True)
            self.assertIsNone(Block.get_spark_session(block))
            block.pipeline.type = 'python'
            self.assertIsNone(Block.get_spark_session(block))

    def test_invalid_spark_configuration_is_not_silently_ignored(self):
        from mage_ai.data_preparation.models.block import Block
        block = SimpleNamespace(spark_init=False, spark=None, global_vars={},
                                pipeline=SimpleNamespace(type='pyspark', spark_config={
                                    'spark_master': 'spark://internal:7077'}))
        with patch('mage_ai.data_preparation.models.block.SPARK_ENABLED', True), \
                patch('mage_ai.data_preparation.models.block.get_spark_session',
                      side_effect=RuntimeError('Cannot connect to configured Spark')):
            with self.assertRaisesRegex(RuntimeError, 'Cannot connect'):
                Block.get_spark_session(block, raise_errors=True)

    def test_batch_execution_requests_spark_even_without_installed_runtime(self):
        from mage_ai.data_preparation.models.block import Block
        block = SimpleNamespace(pipeline=SimpleNamespace(type='pyspark'))
        block.get_spark_session = lambda **kwargs: Block.get_spark_session(block, **kwargs)
        with patch('mage_ai.data_preparation.models.block.SPARK_ENABLED', False), \
                patch('mage_ai.data_preparation.models.block.is_spark_env', return_value=False):
            with self.assertRaisesRegex(ImportError, 'PySpark and Java'):
                Block.enrich_global_vars(block, {})
