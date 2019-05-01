#encoding: utf8
import aiohttp
import asyncio
from termcolor import colored
from requests import get
import re
import time
import logging
import typing
import sys

logger = logging.getLogger(__name__)
ip_regex = re.compile(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}")

def get_proxy_list(target_count: int=100) -> typing.List[str]:
    proxies = set()
    while len(proxies) < target_count:
        try:
            url = 'http://www.89ip.cn/tqdl.html?num={}'.format(target_count)
            html = get(url).text

            new_proxies = set(ip_regex.findall(html))
            logger.info("Got %d new proxies", len(new_proxies))
            proxies = proxies.union(new_proxies)
        except Exception as e:
            logger.exception(e)

        time.sleep(3)
    return proxies

async def visit_once(url: str, proxy: str, semaphore: asyncio.Semaphore, timeout: int=5) -> bool:
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url=url, proxy='http://{}'.format(proxy), timeout=timeout) as resp:
                    logger.info("Proxy %s succeed", proxy)
                    return True
            except:
                logger.warning("Proxy %s failed", proxy)
                return False

def exception_handler(loop, context):
    pass

def visit_count(url: str, count: int=40, max_concurrency: int=40) -> None:
    successful_count = 0
    used_proxies = set()
    proxies = get_proxy_list()
    
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)
    sem = asyncio.Semaphore(max_concurrency)

    while successful_count < count:
        proxies = get_proxy_list() - used_proxies
        logger.info("starting batch with %d proxies", len(proxies))
        tasks = [asyncio.ensure_future(visit_once(url, proxy, sem)) for proxy in proxies]
        successful_count += len(list(filter(None, loop.run_until_complete(asyncio.gather(*tasks)))))
        used_proxies = used_proxies.union(proxies)
        logger.info("%d successful requests using %d proxies", successful_count, len(used_proxies))

    loop.close()

if __name__ == "__main__":
    url = sys.argv[1]
    visit_count(url)