import os

from botocore.config import Config


def client_options(**kwargs):
    """Keep S3-compatible endpoint and signing options consistent across clients."""
    endpoint = (kwargs.get('endpoint_url') or os.getenv('AWS_ENDPOINT_URL_S3')
                or os.getenv('AWS_ENDPOINT'))
    supplied_config = kwargs.get('config')
    s3_options = dict(supplied_config.s3 or {}) if supplied_config is not None else {}
    style = (kwargs.get('addressing_style') or s3_options.get('addressing_style')
             or os.getenv('AWS_S3_ADDRESSING_STYLE')
             or ('path' if endpoint else 'auto'))
    if style not in ('auto', 'path', 'virtual'):
        raise ValueError('S3 addressing_style must be auto, path, or virtual.')
    options = {key: kwargs[key] for key in (
        'aws_access_key_id', 'aws_secret_access_key', 'aws_session_token',
        'region_name', 'verify', 'api_version', 'use_ssl',
    ) if kwargs.get(key) is not None}
    if endpoint:
        options['endpoint_url'] = endpoint
    config = Config(s3={'addressing_style': style}, signature_version='s3v4')
    if supplied_config is not None:
        config = config.merge(supplied_config)
    # Config.merge replaces the entire s3 dictionary; retain both caller options
    # and the resolved addressing style instead of silently dropping either.
    config = config.merge(Config(s3={**s3_options, 'addressing_style': style}))
    options['config'] = config
    return options
