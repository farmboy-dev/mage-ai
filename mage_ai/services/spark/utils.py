from mage_ai.data_preparation.repo_manager import get_repo_config
from mage_ai.server.kernels import KernelName
from mage_ai.services.spark.constants import ComputeServiceUUID, SparkMaster
from mage_ai.shared.utils import is_spark_env


def get_compute_service(
    repo_config=None,
    ignore_active_kernel: bool = False,
    kernel_name: KernelName = None,
) -> ComputeServiceUUID:
    repo_config = repo_config or get_repo_config()
    if (repo_config and is_spark_env() and repo_config.spark_config
            and SparkMaster.LOCAL.value == repo_config.spark_config.get('spark_master')):
        return ComputeServiceUUID.STANDALONE_CLUSTER
    return None
