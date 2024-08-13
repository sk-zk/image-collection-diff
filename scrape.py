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
        heading = table.find_previous_sibling("h3")
        rows = table.find("tbody").find_all("tr")
        for row in rows:
            cells = row.find_all(recursive=False)
            region = cells[0].text.strip()
            period = cells[-1].text.strip()
            if len(cells) > 2:
                camera_type = cells[1].text.strip()
            else:
                camera_type = get_camera_type_from_heading(heading.text.strip())
            region_dict = {
                "region": region,
                "period": period,
                "type": camera_type
            }
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
            camera_type = get_camera_type_from_heading(period)
            subdivision_tags = collection.find_all("span", class_="dl-level-name")
            subdivisions = []

            for subdivision_tag in subdivision_tags:
                subdivision = subdivision_tag.text.strip()
                if subdivision[-1] == ",":
                    subdivision = subdivision[:-1]
                subdivisions.append(subdivision)

            region_dict = {
                "region": region,
                "period": period,
                "subdivisions": subdivisions,
            }
            if camera_type != period:
                region_dict["type"] = camera_type
            regions.append(region_dict)

    return regions


def get_camera_type_from_heading(heading: str) -> str:
    lower = heading.lower()

    if "ipad" in lower:
        return "ipad"

    backpack_strings = ["backpack", "batoh", "rucksack", "バックパック", "背包", "sac à dos",
                        "ryggsäck", "vrsta", "pedestre", "plecak", "ryggsekk", "rugzak",
                        "mochila", "apparati a spalla", "pedone", "hátizsák", "reppu",
                        "ruksak", "Раница", "Σακίδιο"]
    for string in backpack_strings:
        if string in lower:
            return "backpack"

    vehicle_strings = ["vehicle", "vozidlo", "fahrzeug", "車両", "車輛", "véhicules",
                       "fordon", "vozilo", "veículo", "pojazd", "kjøretøy", "voertuig",
                       "vehículo", "veicoli", "veicolo", "jármű", "ajoneuvo", "priemonė",
                       "sõiduk", "transportlīdzeklis", "vehiculelor", "Όχημα"]
    for string in vehicle_strings:
        if string in lower:
            return "vehicle"

    return heading


def main():
    if not os.path.exists("schedules"):
        os.mkdir("schedules")
    countries = get_countries()
    for country in countries:
        schedule = get_country_schedule(country)
        with open(f"schedules/{country}.json", "w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
