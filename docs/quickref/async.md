# async / await (≈ Promises, but nothing runs until awaited)

```python
import asyncio

async def fetch(id: int) -> dict:        # calling it returns a coroutine (≈ an unstarted Promise)
    await asyncio.sleep(0.1)
    return {"id": id}

asyncio.run(main())                      # top-level entry point (FastAPI runs the loop for you)
```

| JS | Python |
|---|---|
| `await Promise.all(ps)` | `await asyncio.gather(*coros)` (results in order) |
| `Promise.allSettled` | `gather(*coros, return_exceptions=True)` → values **or** exception objects |
| `Promise.race` / timeout | `async with asyncio.timeout(2):` → raises `TimeoutError` |
| fire and forget | `task = asyncio.create_task(coro)` (keep a reference!) |
| concurrency limit | `sem = asyncio.Semaphore(5)` + `async with sem:` |

```python
results = await asyncio.gather(*(fetch(i) for i in ids))
ok = [r for r in results if not isinstance(r, Exception)]   # after return_exceptions=True
```

⚠️ Forgetting `await` gives you a coroutine object, not the value (plus a "never awaited" warning).
⚠️ `time.sleep()` / blocking I/O inside `async def` freezes everything; use `await asyncio.sleep()`.
