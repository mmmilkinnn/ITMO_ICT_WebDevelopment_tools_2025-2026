from __future__ import annotations

import asyncio
import os
import time

import aiohttp

from common import URLS, extract_title, prepare_database, save_hackathon_title, split_urls


WORKERS = 3
CLIENT_SESSION: aiohttp.ClientSession | None = None


async def load_html(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
        response.raise_for_status()
        return await response.text(errors="replace")


async def parse_and_save(url: str) -> None:
    if CLIENT_SESSION is None:
        raise RuntimeError("Client session is not initialized")

    html = await load_html(CLIENT_SESSION, url)
    title = extract_title(html)
    row_id = await asyncio.to_thread(save_hackathon_title, url, title, "async")
    print(f"[async] saved hackathon id={row_id}: {title} ({url})")


async def worker(urls: list[str]) -> None:
    for url in urls:
        try:
            await parse_and_save(url)
        except Exception as exc:
            print(f"[async] failed {url}: {exc}")


async def main() -> None:
    workers_count = min(WORKERS, os.cpu_count() or WORKERS, len(URLS))
    chunks = split_urls(URLS, workers_count)
    prepare_database()

    started_at = time.perf_counter()

    headers = {"User-Agent": "Mozilla/5.0 lab2-async-parser"}
    async with aiohttp.ClientSession(headers=headers) as session:
        global CLIENT_SESSION
        CLIENT_SESSION = session
        tasks = [
            asyncio.create_task(worker(chunk))
            for chunk in chunks
        ]
        await asyncio.gather(*tasks)
        CLIENT_SESSION = None

    elapsed = time.perf_counter() - started_at
    print("Approach: async/await + aiohttp")
    print(f"Workers: {workers_count}")
    print(f"Parsed URLs: {len(URLS)}")
    print(f"Time: {elapsed:.6f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
