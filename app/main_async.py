import asyncio

from aiohttp import ClientSession
import json
from random import choice
from aiohttp.web_exceptions import HTTPError, HTTPClientError
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from get_proxies import get_working_proxies_list, get_proxy

REGIONS_IDS = {
    "USA": 143,
    "EUROPE": 65,
    "CANADA": 1677,
    "LATIN_AMERICA_CARRIBEAN": 1637,
    "AUSTRALIA_NEW_ZEALAND_ASIA": 1690,
}

MAIN_PAGE_URL = "https://iwilltravelagain.com"

URL = "https://iwilltravelagain.com/edit/wp-admin/admin-ajax.php"

UA = UserAgent()
HEADERS = {
    "Cookie": "__cfduid=d21792f726322fd0eeabce420fc5c44071599829307",
    "User-Agent": UA.random,
}

proxies_list = get_working_proxies_list(get_proxy())
result = {}


async def get_region_companies_list(region_id, session):
    payload = {
        "action": "get_activities",
        "post_id": region_id,
        "key": "rows_2_grid_activities",
    }

    while True:
        proxy = choice(proxies_list)
        try:
            response = await session.request(
                "POST",
                URL,
                headers=HEADERS,
                data=payload,
                proxy=proxy,
                timeout=30,
            )
            if response.status != 200:
                raise HTTPClientError
            break
        except HTTPError as e:
            print(e)
        except Exception as e:
            print(e)
            print(f"Connection error, looking for another proxy")

    try:
        data = await response.json(content_type=None)
        if type(data) == list:
            return data
        else:
            raise TypeError
    except Exception:
        await get_region_companies_list(region_id, session)


async def get_website_url(link, session):
    attempts = 50
    website_url = ""
    while attempts > 0:
        proxy = choice(proxies_list)
        try:
            await asyncio.sleep(1)

            response = await session.request(
                "GET",
                link,
                proxy=proxy,
                headers=HEADERS,
                timeout=40,
                raise_for_status=True,
            )
            if response.status != 200:
                raise HTTPClientError
            html = await response.text()
            soup = BeautifulSoup(html, "lxml")
            url_list = soup.find("div", class_="block activity-buttons")
            website_url = (
                url_list.find_all("a")[1]
                .get("href")
                .strip()
            )
            break
        except HTTPError as e:
            print(e)
        except Exception as e:
            print(e)
            print("Connection error, looking for another proxy")
            attempts -= 1
    return website_url


def get_taxonomy_data(gathered_data, taxonomy):
    try:
        return gathered_data["taxonomies"][taxonomy]["termString"]
    except Exception:
        return ""


async def company_data(gathered_data, region_name, session):
    data = {
        "title": gathered_data["title"],
        "category": get_taxonomy_data(gathered_data, "activity_category"),
        "location": get_taxonomy_data(gathered_data, "location"),
        "website": await get_website_url(
            f'{MAIN_PAGE_URL}{gathered_data["link"]}', session
        ),
    }
    result[region_name].append(data)
    print(data)
    with open("async_iwilltravelagain.json", "w") as write_file:
        json.dump(result, write_file, indent=4)
    return data


async def gather_tasks():
    async with ClientSession() as session:
        for region in REGIONS_IDS:
            print(f"Start collecting companies for region {region}")
            result[region] = []
            companies = await get_region_companies_list(
                REGIONS_IDS[region], session
            )
            await asyncio.gather(
                *[
                    company_data(
                        gathered_data=data,
                        region_name=region,
                        session=session,
                    )
                    for data in companies
                ]
            )
            result[region].append({"len": len(result[region])})
    return True


if __name__ == "__main__":
    asyncio.run(gather_tasks())
