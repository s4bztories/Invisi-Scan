# scanner_async.py
import asyncio
from typing import List
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

class AsyncPortScanner:
    def __init__(self, target: str, ports: List[int], concurrency: int = 500, timeout: float = 1.0):
        self.target = target
        self.ports = ports
        self.concurrency = concurrency
        self.timeout = timeout

    async def _try_connect(self, port: int, sem: asyncio.Semaphore):
        async with sem:
            try:
                reader, writer = await asyncio.open_connection(self.target, port)
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
                if ok:
                    open_ports.append(port)

        return sorted(open_ports)
