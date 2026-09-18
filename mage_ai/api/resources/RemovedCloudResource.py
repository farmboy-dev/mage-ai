from mage_ai.api.errors import ApiError
from mage_ai.api.resources.GenericResource import GenericResource


def removed_cloud_error():
    error = ApiError.RESOURCE_INVALID.copy()
    error['message'] = (
        'Cloud compute management has been removed. Use local Python or Kubernetes; '
        'configure internal Spark with spark_config in a Python pipeline.'
    )
    raise ApiError(error)


class RemovedCloudResource(GenericResource):
    """Keep legacy routes explicit without importing cloud clients."""

    @classmethod
    def collection(cls, *args, **kwargs):
        removed_cloud_error()

    @classmethod
    def member(cls, *args, **kwargs):
        removed_cloud_error()

    @classmethod
    def create(cls, *args, **kwargs):
        removed_cloud_error()

    def update(self, *args, **kwargs):
        removed_cloud_error()

    def delete(self, *args, **kwargs):
        removed_cloud_error()
