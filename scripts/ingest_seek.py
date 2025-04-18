import requests
from bs4 import BeautifulSoup
import json
import time
import argparse

BASE_URL = "https://www.seek.com.au"

def build_search_url(keywords, location, industry, min_salary, max_salary, page=1):
    url = f"{BASE_URL}/jobs?"
    if keywords:
        url += f"keywords={'+'.join(keywords.split())}&"
    if location:
        url += f"where={'+'.join(location.split())}&"
    if industry:
        url += f"industry={industry}&"
    if min_salary:
        url += f"salaryrange={min_salary}-{max_salary or '999999'}&"
    url += f"page={page}"
    return url

def extract_job_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("article")
    return cards

def parse_job_card(card):
    title_tag = card.find("a", {"data-automation": "jobTitle"})
    title = title_tag.text if title_tag else "N/A"
    link = BASE_URL + title_tag["href"] if title_tag and title_tag.has_attr("href") else None
    company = card.find("span", {"data-automation": "jobCompany"}).text if card.find("span", {"data-automation": "jobCompany"}) else "N/A"
    location = card.find("a", {"data-automation": "jobLocation"}).text if card.find("a", {"data-automation": "jobLocation"}) else "N/A"
    return {
        "title": title,
        "company": company,
        "location": location,
        "link": link
    }

def fetch_seek_jobs(keywords="", location="", industry="", min_salary=None, max_salary=None, max_results=200):
    jobs = []
    page = 1
    while len(jobs) < max_results:
        url = build_search_url(keywords, location, industry, min_salary, max_salary, page)
        print(f"Fetching page {page}: {url}")
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Failed to fetch page {page}")
            break
        cards = extract_job_cards(resp.text)
        if not cards:
            break
        for card in cards:
            job = parse_job_card(card)
            jobs.append(job)
            if len(jobs) >= max_results:
                break
        page += 1
        time.sleep(1)
    return jobs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", type=str, default="")
    parser.add_argument("--location", type=str, default="")
    parser.add_argument("--industry", type=str, default="")
    parser.add_argument("--min_salary", type=int, default=None)
    parser.add_argument("--max_salary", type=int, default=None)
    args = parser.parse_args()

    results = fetch_seek_jobs(
        keywords=args.keywords,
        location=args.location,
        industry=args.industry,
        min_salary=args.min_salary,
        max_salary=args.max_salary
    )

    with open("../data/seek_jobs.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"✅ {len(results)} jobs saved to data/seek_jobs.json")
