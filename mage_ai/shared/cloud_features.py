REMOVED_EXECUTOR_TYPES = frozenset({'ecs', 'azure_container_instance', 'gcp_cloud_run', 'pyspark'})
REMOVED_PROJECT_CONFIGS = frozenset({
    'ecs_config', 'emr_config', 'gcp_cloud_run_config', 'azure_container_instance_config',
})

REMOVED_CONNECTORS = frozenset({
    'tableau', 'teradata',
    'amplitude',
    'chargebee',
    'commercetools',
    'datadog',
    'dynamodb',
    'facebook_ads',
    'freshdesk',
    'front',
    'hubspot',
    'intercom',
    'knowi',
    'linkedin_ads',
    'monday',
    'mode',
    'outreach',
    'paystack',
    'pipedrive',
    'postmark',
    'powerbi',
    'salesforce',
    'stripe',
    'twitter_ads',
    'zendesk',

    'google_ads', 'google_analytics', 'google_search_console',
    'amazon_sqs', 'kinesis', 'google_cloud_pubsub', 'azure_event_hub', 'azure_data_lake',
    'algolia', 'airtable', 'azure_blob_storage', 'bigquery', 'google_cloud_storage', 'google_sheets',
    'redshift', 'snowflake', 'delta_lake_azure',
})


def reject_removed_connector(value):
    if isinstance(value, str) and value in REMOVED_CONNECTORS:
        raise ValueError(
            f'Connector {value!r} has been removed from this internal deployment. '
            'Use a supported internal connector or S3-compatible storage.'
        )


def reject_removed_connector_config(config):
    if not isinstance(config, dict):
        return
    for key in ('data_source', 'data_provider', 'source', 'destination',
                'connector_type', 'data_integration_uuid'):
        reject_removed_connector(config.get(key))
    for key in ('configuration', 'config', 'data_integration', 'template_variables'):
        reject_removed_connector_config(config.get(key))
    template_variables = config.get('template_variables')
    if isinstance(template_variables, dict):
        reject_removed_connector(template_variables.get('uuid'))
        name = template_variables.get('name')
        if isinstance(name, str):
            reject_removed_connector(name.lower().replace(' ', '_'))
    template_path = config.get('template_path')
    if isinstance(template_path, str):
        from pathlib import PurePosixPath

        path = PurePosixPath(template_path)
        reject_removed_connector(path.stem)
        if path.stem == 'gcs' and 'deltalake' in path.parts:
            reject_removed_connector('google_cloud_storage')


def reject_removed_executor(value):
    if value in REMOVED_EXECUTOR_TYPES:
        raise ValueError(
            f'Executor {value!r} has been removed. Use local_python or k8s. '
            'The PySpark kernel is supported with spark_config; executor_type=pyspark was EMR-only.'
        )
