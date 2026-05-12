from __future__ import annotations

import os
import threading
import time
from urllib.request import Request, urlopen

from common import URLS, extract_title, prepare_database, save_hackathon_title, split_urls


WORKERS = 3


def load_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 lab2-threading-parser"})
    with urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_and_save(url: str) -> None:
    html = load_html(url)
    title = extract_title(html)
    row_id = save_hackathon_title(url, title, "threading")
    print(f"[threading] saved hackathon id={row_id}: {title} ({url})")


def worker(urls: list[str]) -> None:
    for url in urls:
        try:
            parse_and_save(url)
        except Exception as exc:
            print(f"[threading] failed {url}: {exc}")


def main() -> None:
    workers_count = min(WORKERS, os.cpu_count() or WORKERS, len(URLS))
    chunks = split_urls(URLS, workers_count)
    prepare_database()

    started_at = time.perf_counter()
    threads = [
        threading.Thread(target=worker, args=(chunk,))
        for chunk in chunks
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    elapsed = time.perf_counter() - started_at
    print("Approach: threading")
    print(f"Workers: {workers_count}")
    print(f"Parsed URLs: {len(URLS)}")
    print(f"Time: {elapsed:.6f} seconds")


if __name__ == "__main__":
    main()
