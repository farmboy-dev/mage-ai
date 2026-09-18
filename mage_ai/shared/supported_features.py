"""Validation of supported execution features before dynamic loading or side effects."""
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


class UnsupportedFeatureError(ValueError):
    pass


def validate_connector(value, kind):
    if kind in ('source', 'destination'):
        from mage_ai.data_integrations.sources.constants import SOURCES
        from mage_ai.data_integrations.destinations.constants import DESTINATIONS
        from mage_ai.data_integrations.utils.settings import get_uuid
        options = SOURCES if kind == 'source' else DESTINATIONS
        supported = {get_uuid(option) for option in options}
    elif kind in ('streaming_source', 'streaming_sink'):
        from mage_ai.streaming.constants import SourceType, SinkType
        supported = {option.value for option in (
            SourceType if kind == 'streaming_source' else SinkType)}
    elif kind == 'data_provider':
        from mage_ai.api.resources.DataProviderResource import DATA_PROVIDERS
        supported = set(DATA_PROVIDERS)
    elif kind == 'data_source':
        from mage_ai.io.base import DataSource
        root = Path(__file__).parents[1] / 'data_preparation' / 'templates'
        supported = {option.value for option in DataSource} | {'generic'}
        for folder in ('data_loaders', 'data_exporters', 'sensors'):
            supported.update(p.stem for p in (root / folder).rglob('*') if p.is_file() and p.suffix in ('.py', '.yaml', '.r', '.jinja')
                             and p.stem != '__init__')
    else:
        raise UnsupportedFeatureError('Unsupported connector context.')
    if not isinstance(value, str) or value not in supported:
        raise UnsupportedFeatureError(f'Unsupported connector for {kind}.')


def validate_template_path(value):
    from mage_ai.data_preparation.templates.constants import TEMPLATES, TEMPLATES_ONLY_FOR_V2
    from mage_ai.extensions.great_expectations.constants import EXTENSION_TEMPLATES
    if not isinstance(value, str):
        raise UnsupportedFeatureError('Unsupported template.')
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '\\' in value:
        raise UnsupportedFeatureError('Unsupported template.')
    supported = {template['path'] for template in
                 TEMPLATES + TEMPLATES_ONLY_FOR_V2 + EXTENSION_TEMPLATES}
    if value not in supported:
        raise UnsupportedFeatureError('Unsupported template.')


def validate_connector_config(config, streaming_kind=None):
    if not isinstance(config, dict):
        return
    for key in ('source', 'destination', 'data_source', 'data_provider'):
        if config.get(key) is not None:
            validate_connector(config[key], key)
    if 'connector_type' in config and streaming_kind:
        validate_connector(config['connector_type'], streaming_kind)
    for key in ('configuration', 'config', 'data_integration'):
        validate_connector_config(config.get(key), streaming_kind=streaming_kind)
    if 'template_path' in config and config.get('template_type') != 'data_integration':
        validate_template_path(config['template_path'])
    if config.get('template_type') == 'data_integration':
        variables = config.get('template_variables') or {}
        path = config.get('template_path', '')
        if path not in ('data_integrations/sources/base', 'data_integrations/destinations/base'):
            raise UnsupportedFeatureError('Unsupported template.')
        kind = path.split('/')[1]
        if kind in ('sources', 'destinations'):
            value = variables.get('uuid') or str(variables.get('name', '')).lower().replace(' ', '_')
            validate_connector(value, 'source' if kind == 'sources' else 'destination')


def validate_executor(value):
    from mage_ai.data_preparation.models.constants import ExecutorType
    if value is not None and (not isinstance(value, str) or value not in set(ExecutorType)):
        raise UnsupportedFeatureError('Unsupported executor.')


def validate_storage_path(value):
    if value is not None and urlsplit(str(value)).scheme not in ('', 's3'):
        raise UnsupportedFeatureError('Unsupported storage scheme. Use a local path or s3 URI.')
