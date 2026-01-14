import asyncio

class BannerGrabber:
    def __init__(self, target: str, timeout: float = 1.0):
        self.target = target
        self.timeout = timeout

    async def _grab_async(self, port: int) -> str:
        try:
            reader, writer = await asyncio.open_connection(self.target, port)
            try:
                data = await asyncio.wait_for(reader.read(4096), timeout=self.timeout)
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
                return data.decode(errors='ignore').strip()
            except Exception:
                try:
                    writer.write(b"GET / HTTP/1.0\r\nHost: %b\r\n\r\n" % self.target.encode())
                    await writer.drain()
                    data = await asyncio.wait_for(reader.read(4096), timeout=self.timeout)
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception:
                        pass
                    return data.decode(errors='ignore').split('\r\n')[0]
                except Exception:
                    return ''
        except Exception:
            return ''

    async def grab_many(self, ports):
        results = {}
        tasks = []
        for p in ports:
            tasks.append((p, asyncio.create_task(self._grab_async(p))))
        for p, t in tasks:
            try:
                results[p] = await t
            except Exception:
                results[p] = ''
        return results
