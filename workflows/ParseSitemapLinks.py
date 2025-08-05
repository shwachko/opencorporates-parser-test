
from temporalio import workflow
from temporalio.common import RetryPolicy
from datetime import timedelta
import asyncio

@workflow.defn(name="ParseSitemapLinksWorkflow")
class ParseSitemapLinks:

    @workflow.run
    async def run(self, input: dict) -> str:


        links = await workflow.execute_activity(
            "fetch_and_parse_gz_xml",
            {"link": input["main_link"], "workflow_id": workflow.info().workflow_id, "run_id": workflow.info().run_id},
            start_to_close_timeout=timedelta(minutes=2),
            heartbeat_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=1,
                maximum_attempts=10,
            ),
            task_queue="fetch-queue"
        )
        handle_list = []
        for link in links["xmls"]:
            handle  = await workflow.start_child_workflow(
                "CrawlXMLWorkflow",
                {"link":link},
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    backoff_coefficient=1,
                    maximum_attempts=0,
                ),
                task_queue="fetch-queue"
            )
            handle_list.append(handle)

        results = await asyncio.gather(*handle_list)
        return sum(results)