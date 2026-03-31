# scanner_async.py
import asyncio
from typing import List
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

class AsyncPortScanner:
    def __init__(self, target: str, ports: List[int], concurrency: int = 500, timeout: float = 1.0, progress_callback=None):
        self.target = target
        self.ports = ports
        self.concurrency = concurrency
        self.timeout = timeout
        self.progress_callback = progress_callback

    async def _try_connect(self, port: int, sem: asyncio.Semaphore):
        async with sem:
            try:
                # Use a specific timeout to ensure we don't hang for long
                fut = asyncio.open_connection(self.target, port)
                reader, writer = await asyncio.wait_for(fut, timeout=self.timeout)
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
                return port, True
            except Exception:
                return port, False

    async def run(self):
        open_ports = []
        sem = asyncio.Semaphore(self.concurrency)
        tasks = []

        # Use the synchronous context manager for Progress (works inside async functions)
        progress = Progress(SpinnerColumn(), TextColumn("Scanning {task.fields[target]}"), BarColumn(), TimeElapsedColumn())
        task_id = progress.add_task("scan", total=len(self.ports), target=self.target)

        with progress:
            for p in self.ports:
                coro = self._try_connect(p, sem)
                task = asyncio.create_task(coro)
                tasks.append(task)

            for fut in asyncio.as_completed(tasks):
                port, ok = await fut
                progress.update(task_id, advance=1)
                
                if self.progress_callback:
                    await self.progress_callback(port, ok)
                
                if ok:
                    open_ports.append(port)

        return sorted(open_ports)
