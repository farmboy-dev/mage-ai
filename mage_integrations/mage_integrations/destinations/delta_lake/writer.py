"""Delta writes using the public delta-rs API and atomic partition replacement."""
from datetime import date, datetime
from decimal import Decimal
from math import isfinite

import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake as write_delta
from deltalake.exceptions import TableNotFoundError

from mage_integrations.destinations.delta_lake.schema import delta_arrow_schema_from_pandas


def try_get_deltatable(table_uri, storage_options=None):
    try:
        return DeltaTable(table_uri, storage_options=storage_options)
    except TableNotFoundError:
        return None


def _partition_predicate(data, columns):
    if any('"' in column for column in columns):
        raise ValueError('Partition overwrite does not support double quotes in column names.')
    clauses = []
    for row in data.select(columns).to_pylist():
        parts = []
        for column in columns:
            identifier = '"' + column.replace('"', '""') + '"'
            value = row[column]
            if value is None:
                parts.append(f'{identifier} IS NULL')
                continue
            if isinstance(value, bool):
                literal = 'true' if value else 'false'
            elif isinstance(value, (int, float, Decimal)):
                if not isfinite(value):
                    raise ValueError('Partition values must be finite.')
                literal = str(value)
            elif isinstance(value, (str, date, datetime)):
                literal = "'" + str(value).replace("'", "''") + "'"
            else:
                raise ValueError('Unsupported partition value type.')
            parts.append(f'{identifier} = {literal}')
        clauses.append('(' + ' AND '.join(parts) + ')')
    return ' OR '.join(dict.fromkeys(clauses))


def write_deltalake(
    table_or_uri, data, *, schema=None, partition_by=None, mode='error',
    overwrite_schema=False, storage_options=None,
):
    if mode not in ('error', 'append', 'overwrite', 'ignore'):
        raise ValueError('Unsupported Delta write mode.')
    if isinstance(data, pd.DataFrame):
        if schema is None:
            data, schema = delta_arrow_schema_from_pandas(data)
        else:
            data = pa.Table.from_pandas(data, schema=schema, preserve_index=False)
    elif isinstance(data, pa.RecordBatch):
        data = pa.Table.from_batches([data], schema=schema)
    elif isinstance(data, pa.RecordBatchReader):
        data = data.read_all()
    elif not isinstance(data, pa.Table):
        if schema is None:
            raise ValueError('A schema is required for iterable data.')
        data = pa.Table.from_batches(list(data), schema=schema)
    if schema is not None:
        data = data.cast(schema)
    if not data.num_rows:
        return

    table = table_or_uri if isinstance(table_or_uri, DeltaTable) else try_get_deltatable(
        table_or_uri, storage_options,
    )
    columns = list(partition_by or [])
    if table is not None:
        existing = table.metadata().partition_columns
        if columns and columns != existing:
            raise ValueError('Partition columns do not match the existing table.')
        columns = existing
    predicate = _partition_predicate(data, columns) if mode == 'overwrite' and columns else None
    write_delta(
        table if table is not None else table_or_uri,
        data, schema=schema, partition_by=columns, mode=mode,
        schema_mode='overwrite' if mode == 'overwrite' and overwrite_schema else None,
        predicate=predicate, storage_options=storage_options, engine='rust',
    )
