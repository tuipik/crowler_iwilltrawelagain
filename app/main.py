import concurrent.futures
import itertools
import json
import time

from random import choice

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from get_proxies import make_working_proxies_dicts


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
proxies_list = make_working_proxies_dicts()
result = {}


def get_region_companies_list(region_id):
    payload = {
        "action": "get_activities",
        "post_id": region_id,
        "key": "rows_2_grid_activities",
    }

    while True:
        proxy = choice(proxies_list)
        try:
            response = requests.request(
                "POST",
                URL,
                headers=HEADERS,
                data=payload,
                proxies=proxy,
                timeout=60,
            )
            if response.status_code != 200:
                raise requests.HTTPError
            break
        except requests.exceptions.HTTPError as e:
            print(e)
        except Exception as e:
            print(e)
            print("Connection error, looking for another proxy")

    try:
        data = response.json(content_type=None)
        if type(data) == list:
            return data
        else:
            raise TypeError
    except Exception:
        get_region_companies_list(region_id)


def get_website_url(link):
    attempts = 30
    website_url = ""
    while attempts > 0:
        proxy = choice(proxies_list)
        try:
            time.sleep(1)
            html = requests.request(
                "GET", link, proxies=proxy, headers=HEADERS, timeout=60
            )
            if html.status_code != 200:
                raise requests.HTTPError
            soup = BeautifulSoup(html.text, "lxml")
            website_url = (
                soup.find("a", title="Click here to Visit Website")
                .get("href")
                .strip()
            )
            break
        except requests.exceptions.HTTPError as e:
            print(e)
        except Exception as e:
            print(e)
            print("Connection error, looking for another proxy")
            attempts -= 1
    return website_url


def get_taxonomy_data(gathered_data, taxonomy):
    try:
        return gathered_data["taxonomies"][taxonomy]["termString"]
    except KeyError:
        return ""


def company_data(gathered_data, region_name):

    data = {
        "title": gathered_data["title"],
        "category": get_taxonomy_data(gathered_data, "activity_category"),
        "location": get_taxonomy_data(gathered_data, "location"),
        "website": get_website_url(f'{MAIN_PAGE_URL}{gathered_data["link"]}'),
    }
    result[region_name].append(data)
    with open("iwilltravelagain.json", "w") as write_file:
        json.dump(result, write_file, indent=4)
    print(data)


if __name__ == "__main__":

    for region in REGIONS_IDS:
        print(f"Start collecting companies for region {region}")
        result[region] = []
        companies = get_region_companies_list(REGIONS_IDS[region])
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=40
        ) as executor:
            executor.map(
                company_data,
                companies,
                itertools.repeat(region, len(companies)),
            )
        result[region].append({"len": len(result[region])})
