from __future__ import annotations

import multiprocessing
import os
import time
from urllib.request import Request, urlopen

from common import URLS, extract_title, prepare_database, save_hackathon_title, split_urls


WORKERS = 3


def load_html(url: str) -> str:
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 lab2-multiprocessing-parser"},
    )
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_and_save(url: str) -> str:
    html = load_html(url)
    title = extract_title(html)
    row_id = save_hackathon_title(url, title, "multiprocessing")
    return f"[multiprocessing] saved hackathon id={row_id}: {title} ({url})"


def worker(urls: list[str]) -> list[str]:
    messages = []
    for url in urls:
        try:
            messages.append(parse_and_save(url))
        except Exception as exc:
            messages.append(f"[multiprocessing] failed {url}: {exc}")
    return messages


def main() -> None:
    workers_count = min(WORKERS, os.cpu_count() or WORKERS, len(URLS))
    chunks = split_urls(URLS, workers_count)
    prepare_database()

    started_at = time.perf_counter()

    with multiprocessing.Pool(processes=workers_count) as pool:
        chunk_results = pool.map(worker, chunks)

    for messages in chunk_results:
        for message in messages:
            print(message)

    elapsed = time.perf_counter() - started_at
    print("Approach: multiprocessing")
    print(f"Workers: {workers_count}")
    print(f"Parsed URLs: {len(URLS)}")
    print(f"Time: {elapsed:.6f} seconds")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
