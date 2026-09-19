import argparse
import json
import sys
from typing import Dict, List

import pandas as pd
import pyarrow as pa

from mage_integrations.destinations.base import Destination as BaseDestination
from mage_integrations.destinations.constants import (
    COLUMN_TYPE_ARRAY,
    COLUMN_TYPE_BOOLEAN,
    COLUMN_TYPE_INTEGER,
    COLUMN_TYPE_NULL,
    COLUMN_TYPE_NUMBER,
    COLUMN_TYPE_OBJECT,
    COLUMN_TYPE_STRING,
    KEY_RECORD,
)
from mage_integrations.destinations.delta_lake.constants import MODE_APPEND
from mage_integrations.destinations.delta_lake.writer import try_get_deltatable, write_deltalake
from mage_integrations.destinations.utils import update_record_with_internal_columns
from mage_integrations.utils.dictionary import merge_dict

MAX_BYTE_SIZE_PER_WRITE = (5 * (1024 * 1024))


class DeltaLake(BaseDestination):
    @property
    def mode(self):
        return self.config.get('mode', MODE_APPEND)

    @property
    def table_name(self):
        return self.config['table']

    def build_client(self):
        raise Exception('Subclasses must implement the build_client method.')

    def build_schema(self, stream: str, df: 'pd.DataFrame'):
        fields = []
        df = df.copy()
        for column_name, properties in self.schemas[stream]['properties'].items():
            types = properties.get('type', [])
            types = [types] if isinstance(types, str) else list(types)
            for option in properties.get('anyOf', []):
                extra = option.get('type', [])
                types.extend([extra] if isinstance(extra, str) else extra)
            kind = next((value for value in types if value != COLUMN_TYPE_NULL), COLUMN_TYPE_STRING)
            arrow_type = {
                COLUMN_TYPE_INTEGER: pa.int64(),
                COLUMN_TYPE_NUMBER: pa.float64(),
                COLUMN_TYPE_BOOLEAN: pa.bool_(),
                COLUMN_TYPE_ARRAY: pa.list_(pa.string()),
            }.get(kind, pa.string())

            def convert(value):
                if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
                    return None
                if kind == COLUMN_TYPE_BOOLEAN:
                    if isinstance(value, bool):
                        return value
                    if isinstance(value, str) and value.lower() in ('true', 'false'):
                        return value.lower() == 'true'
                    raise ValueError(f'Invalid boolean value for {column_name}.')
                if kind == COLUMN_TYPE_INTEGER:
                    converted = int(value)
                    if not isinstance(value, str) and converted != value:
                        raise ValueError(f'Invalid integer value for {column_name}.')
                    return converted
                if kind == COLUMN_TYPE_NUMBER:
                    return float(value)
                if kind == COLUMN_TYPE_ARRAY:
                    if not isinstance(value, list):
                        raise ValueError(f'Expected an array for {column_name}.')
                    return [None if item is None else str(item) for item in value]
                if kind == COLUMN_TYPE_OBJECT:
                    return json.dumps(value)
                return str(value)

            values = [convert(value) for value in df[column_name]]
            nullable = COLUMN_TYPE_NULL in types
            if not nullable and any(value is None for value in values):
                raise ValueError(f'Null value in non-nullable column {column_name}.')
            df[column_name] = pd.Series(values, index=df.index, dtype=object)
            fields.append(pa.field(column_name, arrow_type, nullable=nullable))
        return df, pa.schema(fields)

    def build_storage_options(self) -> Dict:
        raise Exception('Subclasses must implement the build_storage_options method.')

    def build_table_uri(self, stream: str) -> str:
        raise Exception('Subclasses must implement the build_table_uri method.')

    def check_and_create_delta_log(self, stream: str) -> bool:
        raise Exception('Subclasses must implement the check_and_create_delta_log method.')

    def get_table_for_stream(self, stream: str):
        storage_options = self.build_storage_options()
        table_uri = self.build_table_uri(stream)
        return try_get_deltatable(table_uri, storage_options)

    def export_batch_data(self, record_data: List[Dict], stream: str, tags: Dict = None) -> None:
        if not record_data:
            return
        storage_options = self.build_storage_options()
        friendly_table_name = self.config['table']
        table_uri = self.build_table_uri(stream)

        tags = dict(
            records=len(record_data),
            stream=stream,
            table_name=friendly_table_name,
            table_uri=table_uri,
        )

        self.logger.info('Export data started.', tags=tags)

        self.logger.info('Checking if delta logs exist...', tags=tags)
        if self.check_and_create_delta_log(stream):
            self.logger.info('Existing delta logs exist.', tags=tags)
        else:
            self.logger.info('No delta logs exist.', tags=tags)

        self.logger.info(f'Checking if table {friendly_table_name} exists...', tags=tags)
        table = self.get_table_for_stream(stream)
        if table:
            self.logger.info(f'Table {friendly_table_name} already exists.', tags=tags)
        else:
            self.logger.info(f'Table {friendly_table_name} doesn’t exists.', tags=tags)

        for r in record_data:
            r['record'] = update_record_with_internal_columns(r['record'])

        df = pd.DataFrame([d[KEY_RECORD] for d in record_data], dtype=object)
        df_count = len(df.index)

        df, schema = self.build_schema(stream, df)

        idx = 0
        total_byte_size = int(df.memory_usage(deep=True).sum())
        tags2 = merge_dict(tags, dict(
            total_byte_size=total_byte_size,
        ))

        self.logger.info(f'Inserting records for batch {idx} started.', tags=tags2)

        write_deltalake(
            table or table_uri,
            data=df,
            mode=self.mode,
            overwrite_schema=True,
            partition_by=self.partition_keys.get(stream, []),
            schema=schema,
            storage_options=storage_options,
        )

        self.logger.info(f'Inserting records for batch {idx} completed.', tags=tags2)

        self.__after_write_for_batch(stream, idx, tags=tags2)

        tags.update(records_inserted=df_count)

        self.logger.info('Export data completed.', tags=tags)

    def after_write_for_batch(self, stream, index, **kwargs) -> None:
        pass

    def __after_write_for_batch(self, stream, index, **kwargs) -> None:
        tags = kwargs.get('tags', {})

        self.logger.info(f'Handle after write callback for batch {index} started.', tags=tags)
        self.after_write_for_batch(stream, index, **kwargs)
        self.logger.info(f'Handle after write callback for batch {index} completed.', tags=tags)


def main(destination_class):
    destination = destination_class(
        argument_parser=argparse.ArgumentParser(),
        batch_processing=True,
    )
    destination.process(sys.stdin.buffer)
