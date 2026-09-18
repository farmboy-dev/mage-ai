import setuptools


def readme():
    with open('README.md', encoding='utf8') as f:
        README = f.read()
    return README


requirements = []
with open('requirements.txt') as f:
    for line in f.read().splitlines():
        if line.startswith('# extras'):
            break
        requirements.append(line)

setuptools.setup(
    name='mage-ai',
    # NOTE: when you change this, change the value of VERSION in the following file:
    # mage_ai/server/constants.py
    version='0.9.79',
    author='Mage',
    author_email='eng@mage.ai',
    description='Mage is a tool for building and deploying data pipelines.',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/mage-ai/mage-ai',
    packages=setuptools.find_packages('.'),
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    install_requires=requirements,
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'mage=mage_ai.cli.main:app',
        ],
    },
    extras_require={
        'ai': [
            'astor>=0.8.1',
            'langchain==0.2.5',
            'langchain_community==0.2.5',
            'openai==1.82.0',
        ],
        'chroma': [
            'chromadb>=0.4.17',
        ],
        'clickhouse': [
            'clickhouse-connect>=0.10.0',
        ],
        'dbt': [
            'dbt-adapters==1.22.5',
            'dbt-clickhouse==1.10.0',
            'dbt-core==1.10.20',
            'dbt-duckdb==1.10.1',
            'dbt-postgres==1.10.0',
            'dbt-spark==1.10.1',
            'dbt-sqlserver==1.9.0',
            'dbt-trino==1.10.1',
            'trino~=0.326',
        ],
        'hdf5': [
            "tables==3.7.0; python_version < '3.11'",
            "tables==3.10.1; python_version >= '3.11'",
        ],
        'mysql': [
            "mysql-connector-python~=8.4.0; python_version < '3.11'",
            "mysql-connector-python~=9.0.0; python_version >= '3.11'",
        ],
        'oracle': [
            "oracledb==1.3.1; python_version < '3.12'",
            "oracledb==2.4.1; python_version >= '3.12'",
        ],
        'postgres': [
            'psycopg2==2.9.3',
            'psycopg2-binary==2.9.3',
            'sshtunnel==0.4.0',
        ],
        'qdrant': [
            'qdrant-client==1.6.9',
            'sentence-transformers==2.2.2',
        ],
        's3': [
            'boto3==1.26.60',
            'botocore==1.29.60',
        ],
        'spark': [
            'boto3==1.26.60',
            'botocore==1.29.60',
        ],
        'streaming': [
            'confluent-avro~=1.8.0',
            'elasticsearch==8.15.1',
            'influxdb_client==1.36.1',
            'kafka-python==2.3.0',
            'nats-py==2.6.0',
            'nkeys~=0.2.0',
            'opensearch-py==2.0.0',
            'pika==1.3.1',
            'pymongo==4.3.3',
            'requests_aws4auth==1.1.2',
            'stomp.py==8.1.0',
        ],
        'all': [
            'PyGithub==1.59.0',
            'astor>=0.8.1',
            'boto3==1.26.60',
            'botocore==1.29.60',
            'clickhouse-connect>=0.10.0',
            'confluent-avro~=1.8.0',
            'dbt-adapters==1.22.5',
            'dbt-clickhouse==1.10.0',
            'dbt-core==1.10.20',
            'dbt-duckdb==1.10.1',
            'dbt-postgres==1.10.0',
            'dbt-spark==1.10.1',
            'dbt-sqlserver==1.9.0',
            'dbt-trino==1.10.1',
            'duckdb==1.4.3',
            'elasticsearch==8.15.1',
            'great-expectations==0.18.12',
            'influxdb_client==1.36.1',
            'kafka-python==2.3.0',
            'kubernetes==33.1.0',
            'langchain==0.2.5',
            'langchain_community==0.2.5',
            'ldap3==2.9.1',
            'nats-py==2.6.0',
            'nkeys~=0.2.0',
            'openai==1.82.0',
            'opensearch-py==2.0.0',
            'opentelemetry-api>=1.40.0',
            'opentelemetry-exporter-otlp>=1.40.0',
            'opentelemetry-exporter-prometheus>=0.61b0',
            'opentelemetry-instrumentation-sqlalchemy>=0.61b0',
            'opentelemetry-instrumentation-tornado>=0.61b0',
            'oracledb==1.3.1',
            'pika==1.3.1',
            'pinotdb==5.6.0',
            'prometheus_client>=0.18.0',
            'protobuf>=6.0,<7',
            'psycopg2-binary==2.9.3',
            'psycopg2==2.9.3',
            'pydruid==0.6.5',
            'pymongo==4.3.3',
            "pyodbc==4.0.35; python_version < '3.12'",
            "pyodbc==5.0.1; python_version >= '3.12'",
            'lxml==4.9.4',
            'requests_aws4auth==1.1.2',
            'sshtunnel==0.4.0',
            'stomp.py==8.1.0',
            'thefuzz[speedup]==0.19.0',
            'trino~=0.326',
        ],
    },
)
