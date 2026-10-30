import asyncio
from typing import TypedDict
from urllib.parse import urljoin, urlsplit

import aiohttp
from bs4 import BeautifulSoup, Tag


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def normalize_url(url):
    parts = urlsplit(url)
    full_path = f"{parts.netloc}{parts.path}"
    full_path = full_path.rstrip("/")
    return full_path.lower()


def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("h1") or soup.find("h2")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    p_tag = main.find("p") if isinstance(main, Tag) else None
    if p_tag is None:
        p_tag = soup.find("p")
    return p_tag.get_text(strip=True) if isinstance(p_tag, Tag) else ""


def get_urls_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for anchor in soup.find_all("a"):
        if not isinstance(anchor, Tag):
            continue
        href = anchor.get("href")
        if isinstance(href, str) and href.strip():
            urls.append(urljoin(base_url, href.strip()))
    return urls


def get_images_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue
        src = img.get("src")
        if isinstance(src, str) and src.strip():
            urls.append(urljoin(base_url, src.strip()))
    return urls


def extract_page_data(html: str, page_url: str) -> PageData:
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }


class AsyncCrawler:
    def __init__(self, base_url, max_concurrency=1, max_pages=10):
        self.base_url = base_url
        self.base_domain = urlsplit(base_url).netloc.lower()
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session = None
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url):
        async with self.lock:
            if self.should_stop:
                return False
            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False
            if normalized_url in self.visited:
                return False
            self.visited.add(normalized_url)
            return True

    async def get_html(self, url):
        async with self.session.get(
            url, headers={"User-Agent": "BootCrawler/1.0"}
        ) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                raise ValueError(f"expected text/html, got {content_type!r} for {url}")

            return await response.text()

    async def crawl_page(self, current_url):
        if self.should_stop:
            return

        if urlsplit(current_url).netloc.lower() != self.base_domain:
            return

        normalized_url = normalize_url(current_url)
        if not await self.add_page_visit(normalized_url):
            return

        async with self.semaphore:
            print(f"crawling: {current_url}")
            try:
                html = await self.get_html(current_url)
            except Exception as e:
                print(f"error fetching {current_url}: {e}")
                return

            data = extract_page_data(html, current_url)
            async with self.lock:
                self.page_data[normalized_url] = data

        tasks = []
        for next_url in data["outgoing_links"]:
            task = asyncio.create_task(self.crawl_page(next_url))
            self.all_tasks.add(task)
            tasks.append(task)
        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                self.all_tasks.discard(task)

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url, max_concurrency=5, max_pages=10):
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
