from mage_ai.services.spark.api.base import BaseAPI
from mage_ai.services.spark.api.local import LocalAPI


class API:
    @classmethod
    def build(
        self,
        all_applications: bool = True,
        application_id: str = None,
        application_spark_ui_url: str = None,
        repo_config=None,
        spark_session=None,
    ) -> BaseAPI:
        return LocalAPI(
            all_applications=all_applications,
            spark_session=spark_session,
            repo_config=repo_config,
            application_id=application_id,
            application_spark_ui_url=application_spark_ui_url,
        )
