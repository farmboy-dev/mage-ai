from jupyter_client import KernelClient, KernelManager
from jupyter_client.kernelspec import NoSuchKernel

from mage_ai.server.kernels import DEFAULT_KERNEL_NAME, KernelName, kernel_managers
from mage_ai.server.logger import Logger

logger = Logger().new_server_logger(__name__)


class ActiveKernel:
    def __init__(self):
        self.kernel = kernel_managers[DEFAULT_KERNEL_NAME]
        self.kernel_client = self.kernel.client()


active_kernel = ActiveKernel()


def switch_active_kernel(
    kernel_name: KernelName,
) -> None:
    """
    Switches the active kernel to the specified kernel name, handling its startup and
    shutdown.

    This function switches the active kernel to the specified kernel name, shutting down any
    currently active kernel and starting the new kernel. It also updates the active kernel and
    its client. PySpark uses a local IPython kernel with internal Spark configuration.

    This method logs various information and handles exceptions for different scenarios.

    Args:
        kernel_name (KernelName): The name of the kernel to switch to.

    Returns:
        None: This function does not return anything.

    Raises:
        NoSuchKernel: If the specified kernel is not available.

    Note:
        Ensure the necessary dependencies and configurations are set up for the desired kernels.
    """
    logger.info(f'Switch active kernel: {kernel_name}')
    if kernel_managers[kernel_name].is_alive():
        logger.info(f'Kernel {kernel_name} is already alive.')
        active_kernel.kernel = kernel_managers[kernel_name]
        active_kernel.kernel_client = active_kernel.kernel.client()
        return

    for kernel in kernel_managers.values():
        if kernel.is_alive():
            logger.info(f'Shut down current kernel {kernel}.')
            kernel.request_shutdown()

    try:
        new_kernel = kernel_managers[kernel_name]
        new_kernel.start_kernel()
        active_kernel.kernel = new_kernel
        active_kernel.kernel_client = new_kernel.client()
    except NoSuchKernel:
        raise


def get_active_kernel() -> KernelManager:
    return active_kernel.kernel


def get_active_kernel_name() -> str:
    return active_kernel.kernel.kernel_name


def get_active_kernel_client() -> KernelClient:
    return active_kernel.kernel_client


def interrupt_kernel() -> None:
    active_kernel.kernel.interrupt_kernel()


def restart_kernel() -> None:
    active_kernel.kernel.restart_kernel()
    active_kernel.kernel_client = active_kernel.kernel.client()


def start_kernel() -> None:
    active_kernel.kernel.start_kernel()
    active_kernel.kernel_client = active_kernel.kernel.client()
