import os
from typing import Optional


class SettingsBackend:
    """
    Base settings backend class. A settings backend is a read-only storage of Mage settings.
    The source of the configuration settings is dependent on the specific loader. The default source
    are environment variables.
    """
    backend_type = None

    def get(self, key: str, **kwargs) -> Optional[str]:
        """
        Loads the configuration setting stored under `key`.

        Args:
            key (str): Name of the setting to load

        Returns:
            Any: The setting value stored under `key` in the configuration manager. If key
                 doesn't exist, returns None.
        """
        value = self._get(key, **kwargs)  # noqa: E1128
        if value is None:
            value = os.getenv(key)
        if value is None:
            value = kwargs.get('default')
        return value

    def _get(self, key: str, **kwargs) -> Optional[str]:
        """
        Loads the configuration setting stored under `key`.

        Args:
            key (str): Name of the setting to load

        Returns:
            Any: The setting value stored under `key` in the configuration manager. If key
                 doesn't exist, returns None.
        """
        return None
