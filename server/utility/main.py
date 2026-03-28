import asyncio
from typing import AsyncIterable, Awaitable, Callable, Optional, Iterator

async def iterate_tokens_async(
    generator_callback: Callable[..., Iterator[str]],
    cancel_event: Optional[asyncio.Event] | None = None,
    *args, **kwargs
    ) -> AsyncIterable[str]:
    """
    ### Iterate Tokens Asynchronously from Synchronous Generator \n
    This method runs the token streaming from generator_callback (sync) in a separate thread and yields tokens asynchronously. \n
    ***Useful for bridging synchronous token generators (like model inference) into an asynchronous workflow***
    
    **Parameters:** \n
    - `generator_callback`: A callable that initiates the token streaming. Return an asynchronous generator of tokens (by `yield`)
    - `cancel_event`: An optional `asyncio.Event` that can be set to signal cancellation of the token streaming. If this event is set, the method will stop yielding tokens and exit.
    
    **Note:** 
    - Token streaming function must yield and not return - It can be a model or any generator function that produces tokens synchronously. \n
    - Function should be called inside an async context, as it requires an active event loop in which tokens are returned.
    
    **Usage:**
```python
    async for token in iterate_tokens_async(
        generator_callback=my_sync_token_generator, 
        cancel_event=my_cancel_event
    ):
        print(token)
```"""
    
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue(maxsize=32)
    stream_done = object()
    def producer():
        try:
            for token in generator_callback(*args, **kwargs):
                if cancel_event and cancel_event.is_set():
                    break
                fut = asyncio.run_coroutine_threadsafe(queue.put(token), loop)
                fut.result()
        except Exception as exc:
            fut = asyncio.run_coroutine_threadsafe(queue.put(exc), loop)
            fut.result()
        finally:
            fut = asyncio.run_coroutine_threadsafe(queue.put(stream_done), loop)
            fut.result()
    producer_task = asyncio.create_task(asyncio.to_thread(producer))
    
    try:
        while True:
            item = await queue.get()
            if item is stream_done:
                break
            if isinstance(item, Exception):
                raise item
            yield item
    finally:
        if cancel_event:
            cancel_event.set()
        await producer_task
    