import os
import unittest
from unittest.mock import patch

from mage_ai.settings import Settings


class SettingsBackendTest(unittest.TestCase):
    def test_environment_and_default(self):
        settings = Settings()
        settings.set_settings_backend()
        with patch.dict(os.environ, {'MAGE_TEST_SETTING': 'configured'}, clear=True):
            self.assertEqual(settings.get_value('MAGE_TEST_SETTING', 'fallback'), 'configured')
            self.assertEqual(settings.get_value('MAGE_TEST_MISSING', 'fallback'), 'fallback')
            self.assertIsNone(settings.get_value('MAGE_TEST_MISSING'))

    def test_unknown_backend_does_not_initialize_client(self):
        settings = Settings()
        original = settings.settings_backend
        with patch('boto3.client') as client:
            for kwargs in ({'backend_type': 'unknown_backend'}, {'prefix': 'test'}):
                with self.subTest(kwargs=kwargs):
                    with self.assertRaisesRegex(ValueError, 'Unsupported settings backend'):
                        settings.set_settings_backend(**kwargs)
            client.assert_not_called()
        self.assertIs(settings.settings_backend, original)
