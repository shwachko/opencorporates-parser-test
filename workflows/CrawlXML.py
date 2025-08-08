
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta

import asyncio

@workflow.defn(name="CrawlXMLWorkflow")
class CrawlXMLWorkflow:

    def __init__(self):
        self.pending_links: int = 0
        self.signal_received = asyncio.Event()

    @workflow.signal
    async def add_links(self, chunk: int):
        self.pending_links += chunk
        self.signal_received.set()

    @workflow.run
    async def run(self, input: dict) -> str:

        await workflow.execute_activity(
            "fetch_and_parse_gz_xml",
            {"link": input["link"], "workflow_id": workflow.info().workflow_id, "run_id": workflow.info().run_id},
            start_to_close_timeout=timedelta(minutes=2),
            heartbeat_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=1,
                maximum_attempts=10,
            ),
            task_queue="fetch-queue"
        )

        await self.signal_received.wait()

        return self.pending_links