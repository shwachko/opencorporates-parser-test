import asyncio
import os
import signal
import logging

from temporalio.worker import Worker

from workflows.ParseSitemapLinks import ParseSitemapLinks
from workflows.CrawlXML import CrawlXMLWorkflow

from activities.fetch_and_parse_gz_xml import fetch_and_parse_gz_xml


from client import get_temporal_client

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

async def wait_for_temporal():
    while True:
        try:
            client = await get_temporal_client()

            logger.info("Connected to Temporal")
            return client
        except Exception:
            logger.exception("Error connecting to Temporal, retrying in 3s...")
            await asyncio.sleep(3)

async def main():
    client = await wait_for_temporal()

    stop_event = asyncio.Event()

    def handle_shutdown():
        logger.info("Shutdown signal received, stopping worker gracefully...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown)
    loop.add_signal_handler(signal.SIGINT, handle_shutdown)

    queue = os.getenv("QUEUE")

    if queue == "fetch-queue":
        workflows = [ParseSitemapLinks, CrawlXMLWorkflow]
        activities = [fetch_and_parse_gz_xml]
    else:
        raise ValueError(f"Unknown queue: {queue}")

    worker = Worker(
        client,
        task_queue=queue,
        workflows=workflows,
        activities=activities,
        max_concurrent_activities=5,
        max_concurrent_workflow_tasks=5,
        max_concurrent_activity_task_polls=2,
        max_concurrent_workflow_task_polls=2,
        max_activities_per_second=10,
        max_task_queue_activities_per_second=100,


    )

    async with worker:
        logger.info("Worker started and running. Waiting for shutdown signal...")
        await stop_event.wait()
        logger.info("Worker shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
