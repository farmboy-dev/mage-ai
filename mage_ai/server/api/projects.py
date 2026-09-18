from mage_ai.server.api.base import BaseHandler
from mage_ai.server.constants import VERSION
from mage_ai.settings.repo import get_repo_path


class ApiProjectsHandler(BaseHandler):
    async def get(self):
        parts = get_repo_path().split('/')
        collection = [
            dict(
                latest_version=VERSION,
                name=parts[-1],
                version=VERSION,
            ),
        ]
        self.write(dict(projects=collection))
