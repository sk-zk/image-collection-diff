import json
import os
from typing import List

import requests
from bs4 import BeautifulSoup


def get_countries() -> List[str]:
    response = requests.get("https://maps.apple.com/imagecollection/locations/")
    html = response.text
    soup = BeautifulSoup(html)
    dropdown = soup.find(id="country-dropdown")
    countries = [x["value"] for x in dropdown.findChildren()]
    return countries


def get_country_schedule(country: str):
    response = requests.get(f"https://maps.apple.com/imagecollection/{country}/",
                            headers={
                                "Accept-Language": "en-US"
                            })
    html = response.text
    soup = BeautifulSoup(html)

    tables = soup.find_all("table")
    if len(tables) > 0:
        regions = extract_table_schedule(tables)
    else:
        regions = extract_detailed_schedule(soup)

    return regions


def extract_table_schedule(tables) -> List[dict]:
    regions = []
    for table in tables:
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            cells = row.find_all(recursive=False)
            region = cells[0].text.strip()
            period = cells[-1].text.strip()
            if len(cells) > 2:
                camera_type = cells[1].text.strip()
            else:
                camera_type = None
            region_dict = {
                "region": region,
                "period": period
            }
            if camera_type:
                region_dict["type"] = camera_type
            regions.append(region_dict)
    return regions


def extract_detailed_schedule(soup) -> List[dict]:
    regions = []
    sections = soup.find_all(class_="dl-period")
    for section in sections:
        region = section.find(class_="driving-dates").text.strip()
        collections = section.find_all(class_="dl-level-2")

        for collection in collections:
            period = section.find("h5").text.strip()
            subdivision_tags = collection.find_all("span", class_="dl-level-name")
            subdivisions = []

            for subdivision_tag in subdivision_tags:
                subdivision = subdivision_tag.text.strip()
                if subdivision[-1] == ",":
                    subdivision = subdivision[:-1]
                subdivisions.append(subdivision)

            regions.append({
                "region": region,
                "period": period,
                "subdivisions": subdivisions,
            })
    return regions


def main():
    os.mkdir("schedules")
    countries = get_countries()
    for country in countries:
        schedule = get_country_schedule(country)
        with open(f"schedules/{country}.json", "w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
