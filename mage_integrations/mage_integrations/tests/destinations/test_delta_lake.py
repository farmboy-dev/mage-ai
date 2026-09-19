import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable

from mage_integrations.destinations.delta_lake_s3 import DeltaLakeS3
from mage_integrations.destinations.delta_lake.writer import try_get_deltatable, write_deltalake


class DeltaWriterTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = str(Path(self.directory.name) / 'table')

    def ids(self):
        return sorted(DeltaTable(self.path).to_pyarrow_table().column('id').to_pylist())

    def test_create_append_ignore_error_and_overwrite(self):
        write_deltalake(self.path, pa.table({'id': [1]}))
        write_deltalake(self.path, pa.table({'id': [2]}), mode='append')
        self.assertEqual(self.ids(), [1, 2])
        write_deltalake(self.path, pa.table({'id': [3]}), mode='ignore')
        self.assertEqual(self.ids(), [1, 2])
        with self.assertRaises(Exception):
            write_deltalake(self.path, pa.table({'id': [4]}))
        self.assertEqual(self.ids(), [1, 2])
        write_deltalake(self.path, pa.table({'id': [5]}), mode='overwrite')
        self.assertEqual(self.ids(), [5])

    def test_compound_partition_overwrite_with_null_and_quotes(self):
        schema = pa.schema([('id', pa.int64()), ('group_name', pa.string()), ('part', pa.int64())])
        old = pa.Table.from_pylist([
            {'id': 1, 'group_name': "a'b", 'part': 1},
            {'id': 2, 'group_name': "a'b", 'part': 2},
            {'id': 3, 'group_name': None, 'part': 1},
            {'id': 4, 'group_name': 'keep', 'part': 1},
        ], schema=schema)
        write_deltalake(self.path, old, partition_by=['group_name', 'part'])
        replacement = pa.Table.from_pylist([
            {'id': 5, 'group_name': "a'b", 'part': 1},
            {'id': 6, 'group_name': None, 'part': 1},
        ], schema=schema)
        write_deltalake(self.path, replacement, mode='overwrite')
        self.assertEqual(self.ids(), [2, 4, 5, 6])
        self.assertEqual(DeltaTable(self.path, version=0).to_pyarrow_table().num_rows, 4)

    def test_schema_change_is_explicit(self):
        write_deltalake(self.path, pa.table({'id': [1]}))
        with self.assertRaises(Exception):
            write_deltalake(self.path, pa.table({'id': [2], 'new': ['x']}), mode='append')
        self.assertEqual(self.ids(), [1])
        write_deltalake(self.path, pa.table({'id': [2], 'new': ['x']}),
                        mode='overwrite', overwrite_schema=True)
        self.assertEqual(self.ids(), [2])
        self.assertIn('new', DeltaTable(self.path).schema().to_pyarrow().names)

    def test_empty_input_does_not_overwrite(self):
        write_deltalake(self.path, pa.table({'id': [1]}))
        write_deltalake(self.path, pa.table({'id': pa.array([], type=pa.int64())}), mode='overwrite')
        self.assertEqual(self.ids(), [1])
        self.assertEqual(DeltaTable(self.path).version(), 0)

    def test_dataframe_timestamp_and_explicit_schema(self):
        frame = pd.DataFrame({'id': [1], 'time': pd.to_datetime(['2024-01-01'])})
        write_deltalake(self.path, frame)
        self.assertEqual(DeltaTable(self.path).schema().to_pyarrow().field('time').type.unit, 'us')
        write_deltalake(self.path, pd.DataFrame({'id': [2], 'time': pd.to_datetime(['2024-01-02'])}),
                        schema=DeltaTable(self.path).schema().to_pyarrow(), mode='append')
        self.assertEqual(self.ids(), [1, 2])

    def test_lookup_only_swallows_missing_table(self):
        self.assertIsNone(try_get_deltatable(self.path))
        with patch('mage_integrations.destinations.delta_lake.writer.DeltaTable',
                   side_effect=OSError('Access denied')):
            with self.assertRaisesRegex(OSError, 'Access denied'):
                try_get_deltatable(self.path)

    def test_record_batch_reader(self):
        batch = pa.record_batch({'id': [1]})
        write_deltalake(self.path, pa.RecordBatchReader.from_batches(batch.schema, [batch]))
        self.assertEqual(self.ids(), [1])

    def test_unsupported_partition_name_fails_before_commit(self):
        data = pa.table({'id': [1], 'bad"name': ['a']})
        write_deltalake(self.path, data, partition_by=['bad"name'])
        with self.assertRaisesRegex(ValueError, 'double quotes'):
            write_deltalake(self.path, data, mode='overwrite')
        self.assertEqual(DeltaTable(self.path).version(), 0)

    def test_declared_arrays_objects_and_nullable_booleans(self):
        destination = DeltaLakeS3(config={})
        destination.schemas = {'s': {'properties': {
            'items': {'type': 'array'}, 'payload': {'type': 'object'},
            'flag': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]},
        }}}
        data, schema = destination.build_schema('s', pd.DataFrame([
            {'items': ['a', 2, None], 'payload': {'x': 1}, 'flag': False},
            {'items': [], 'payload': {}, 'flag': None},
        ], dtype=object))
        write_deltalake(self.path, data, schema=schema)
        rows = DeltaTable(self.path).to_pyarrow_table().to_pylist()
        self.assertEqual(rows[0]['items'], ['a', '2', None])
        self.assertEqual(rows[0]['payload'], '{"x": 1}')
        self.assertIs(rows[0]['flag'], False)
        self.assertIsNone(rows[1]['flag'])

    def test_invalid_declared_values_are_rejected(self):
        destination = DeltaLakeS3(config={})
        for kind, value in [('boolean', 'not-a-boolean'), ('integer', 1.5), ('integer', None)]:
            with self.subTest(kind=kind, value=value):
                destination.schemas = {'s': {'properties': {'value': {'type': kind}}}}
                with self.assertRaises(ValueError):
                    destination.build_schema('s', pd.DataFrame({'value': [value]}, dtype=object))
