import asyncio
import os
from temporalio.client import Client

_temporal_client = None
_client_lock = asyncio.Lock()

async def get_temporal_client() -> Client:
    global _temporal_client
    async with _client_lock:
        if _temporal_client is None:

            _temporal_client = await Client.connect(
                os.getenv("LOCAL_TEMPORAL_ENDPOINT"),
                namespace=os.getenv("DEFAULT_NAMESPACE"),
            )

    return _temporal_client
