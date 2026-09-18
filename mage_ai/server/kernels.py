from jupyter_client import KernelManager
from jupyter_client.session import Session
from jupyter_client.kernelspec import KernelSpecManager

from mage_ai.data_preparation.models.constants import PipelineType
from mage_ai.shared.enum import StrEnum


class KernelName(StrEnum):
    PYSPARK = 'pysparkkernel'
    PYTHON3 = 'python3'


PIPELINE_TO_KERNEL_NAME = {
    PipelineType.INTEGRATION: KernelName.PYTHON3,
    PipelineType.DATABRICKS: KernelName.PYTHON3,
    PipelineType.PYTHON: KernelName.PYTHON3,
    PipelineType.PYSPARK: KernelName.PYSPARK,
    PipelineType.STREAMING: KernelName.PYTHON3,
}


DEFAULT_KERNEL_NAME = KernelName.PYTHON3


class InternalSparkKernelSpecManager(KernelSpecManager):
    def get_kernel_spec(self, kernel_name):
        if kernel_name == KernelName.PYSPARK:
            spec = super().get_kernel_spec(KernelName.PYTHON3)
            spec.display_name = 'PySpark'
            return spec
        return super().get_kernel_spec(kernel_name)


kernel_managers = dict(
    python3=KernelManager(
        session=Session(key=bytes()),
    ),
    pysparkkernel=KernelManager(
        kernel_name=KernelName.PYSPARK,
        kernel_spec_manager=InternalSparkKernelSpecManager(),
        session=Session(key=bytes()),
    ),
)
