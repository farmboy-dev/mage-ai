from typing import Any


class UsageStatisticLogger:
    """Compatibility hooks for callers; usage statistics collection and transmission are removed."""

    def __init__(self, context_data: Any = None, project=None, repo_path: Any = None):
        pass

    async def block_create(
        self,
        block: Any,
        block_action_object: Any = None,
        custom_template: Any = None,
        payload_config: Any = None,
        pipeline: Any = None,
        replicated_block: Any = None,
    ) -> bool:
        return False

    @property
    def help_improve_mage(self) -> bool:
        return False

    async def chart_impression(self, chart_config: Any) -> bool:
        return False

    async def custom_template_create(self, custom_template: Any) -> bool:
        return False

    async def project_deny_improve_mage(self, project_uuid) -> bool:
        return False

    async def error(
        self,
        event_name: Any,
        code: Any = None,
        errors: Any = None,
        message: Any = None,
        type: Any = None,
        operation: Any = None,
        resource: Any = None,
        resource_id: Any = None,
        resource_parent: Any = None,
        resource_parent_id: Any = None,
    ) -> bool:
        return False

    async def project_impression(self) -> bool:
        return False

    def pipeline_runs_impression_sync(self, count_func: Any) -> bool:
        return False

    async def pipeline_runs_impression(self, count_func: Any) -> bool:
        return False

    async def pipeline_create(
        self,
        pipeline: Any,
        clone_pipeline_uuid: Any = None,
        llm_payload: Any = None,
        template_uuid: Any = None,
    ) -> bool:
        return False

    async def pipelines_impression(self, count_func: Any) -> bool:
        return False

    async def users_impression(self) -> bool:
        return False

    def pipeline_run_ended_data(self, pipeline_run: Any):
        return {}

    async def pipeline_run_ended(self, pipeline_run: Any) -> bool:
        return False

    def pipeline_run_ended_sync(self, pipeline_run: Any) -> bool:
        return False

    async def block_run_ended(self, block_run: Any) -> bool:
        return False
