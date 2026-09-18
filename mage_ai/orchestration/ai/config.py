import os
from dataclasses import dataclass
from urllib.parse import urlsplit

from mage_ai.data_preparation.models.constants import AIMode
from mage_ai.shared.config import BaseConfig


@dataclass
class OpenAIConfig(BaseConfig):
    openai_api_key: str = None
    openai_base_url: str = None
    openai_model: str = None

    @classmethod
    def resolve(cls, repo_config, fallback=None):
        fallback = fallback or cls.load(
            config=(repo_config.ai_config or {}).get('open_ai_config') or {},
        )
        return cls(**{
            key: getattr(repo_config, key, None) or getattr(fallback, key, None) or os.getenv(env)
            for key, env in (
                ('openai_api_key', 'OPENAI_API_KEY'),
                ('openai_base_url', 'OPENAI_BASE_URL'),
                ('openai_model', 'OPENAI_MODEL'),
            )
        })

    def validate(self):
        if (not isinstance(self.openai_base_url, str) or not self.openai_base_url.strip()
                or not isinstance(self.openai_model, str) or not self.openai_model.strip()):
            raise ValueError('Configure an OpenAI-compatible base URL and model before using AI.')
        url = urlsplit(self.openai_base_url)
        # Accessing port validates non-numeric and out-of-range port values.
        port = url.port
        if (url.scheme not in ('http', 'https') or not url.hostname
                or port == 0 or any(char.isspace() for char in self.openai_base_url)
                or url.username or url.password or url.query or url.fragment):
            raise ValueError('AI base URL must be an HTTP(S) URL without credentials or query.')

    @property
    def configured(self):
        try:
            self.validate()
            return True
        except ValueError:
            return False


@dataclass
class HuggingFaceConfig(BaseConfig):
    huggingface_api: str = None
    huggingface_inference_api_token: str = None


@dataclass
class AIConfig(BaseConfig):
    mode: AIMode = AIMode.OPEN_AI
    open_ai_config: OpenAIConfig = OpenAIConfig
    hugging_face_config: HuggingFaceConfig = HuggingFaceConfig
