import asyncio

from aiohttp import ClientSession
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

UA = UserAgent()

HEADERS = {
    "Cookie": "__cfduid=d21792f726322fd0eeabce420fc5c44071599829307",
    "User-Agent": UA.random,
}

URL = "https://iwilltravelagain.com"


async def check_proxies(proxy, url, headers, session):
    try:
        await asyncio.sleep(1)
        response = await session.request(
            method="GET", url=url, proxy=proxy, headers=headers, timeout=30
        )
        return proxy
    except requests.exceptions.HTTPError:
        pass
    except Exception:
        pass


def get_proxy():
    print("start collect free proxies")
    response = requests.get("https://sslproxies.org/")
    soup = BeautifulSoup(response.content, "lxml")
    raw_proxies_list = list(
        zip(
            map(
                lambda x: x.text,
                soup.find("table", id="proxylisttable").findAll("td")[::8],
            ),
            map(
                lambda x: x.text,
                soup.find("table", id="proxylisttable").findAll("td")[1::8],
            ),
        )
    )

    proxy = [f"http://{item[0]}:{item[1]}" for item in raw_proxies_list]
    return proxy


async def gather_tasks(proxies_list):
    async with ClientSession() as session:
        return await asyncio.gather(
            *[
                check_proxies(
                    proxy=proxy, url=URL, headers=HEADERS, session=session
                )
                for proxy in proxies_list
            ]
        )


def get_working_proxies_list(proxies_list):
    loop = asyncio.get_event_loop()
    checked_proxies = loop.run_until_complete(gather_tasks(proxies_list))
    loop.close()
    clean_checked_proxies_list = [proxy for proxy in checked_proxies if proxy]
    print(f'Got {len(clean_checked_proxies_list)} proxies')
    return clean_checked_proxies_list


def make_working_proxies_dicts():
    free_proxies_list = get_proxy()
    proxies = get_working_proxies_list(free_proxies_list)

    return [
        {
            "http": item,
            "https": item,
        }
        for item in proxies
    ]
