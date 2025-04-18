from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import argparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException


from urllib.parse import quote_plus

def build_url(keywords="", location="", min_salary=None, page=1):
    keyword_slug = "-".join(keywords.lower().split())
    location_slug = quote_plus(location)

    url = f"https://www.seek.com.au/{keyword_slug}-jobs/in-{location_slug}"
    url += f"?page={page}&sortmode=ListedDate"

    if min_salary:
        url += f"&salaryrange={min_salary}-&salarytype=annual"

    return url

def fetch_jobs(driver, max_jobs=20):
    jobs = []
    page = 1

    while len(jobs) < max_jobs:
        url = build_url(args.keywords, args.location, args.min_salary, page)
        print(f"🔍 Visiting {url}")
        
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #time.sleep(3)

        #time.sleep(10)



        # 🔍 Dump the HTML of the first page for inspection
        if page == 1:
            with open("seek_debug_page1.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

        # Wait until job titles are visible
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-automation='jobTitle']"))
            )
            print("✅ Job cards are now visible.")
        except TimeoutException:
            print("⚠️ Job titles not loaded after waiting.")
            return []


        job_elements = driver.find_elements(By.CSS_SELECTOR, "a[data-automation='jobTitle']")

        for title_elem in job_elements:
            try:
                title = title_elem.text
                link = title_elem.get_attribute("href")

                jobs.append({
                    "title": title,
                    "link": link
                })
            except Exception as e:
                print("⚠️ Skipping job due to:", e)


        if len(jobs) >= max_jobs:
            break

        page += 1
        #time.sleep(2)

    return jobs

def enrich_jobs(driver, jobs):
    print(f"\n🔁 Visiting {len(jobs)} job detail pages to extract more info...\n")

    enriched = []

    for job in jobs:
        try:
            driver.get(job["link"])
            time.sleep(3)

            # Wait for the job description to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation='jobAdDetails']"))
            )

            try:
                description = driver.find_element(By.CSS_SELECTOR, "div[data-automation='jobAdDetails']").text
            except:
                description = ""

            try:
                company = driver.find_element(By.CSS_SELECTOR, "[data-automation='advertiser-name']").text
            except:
                company = "N/A"

            try:
                location = driver.find_element(By.CSS_SELECTOR, "[data-automation='job-detail-location']").text
            except:
                location = "N/A"

            job.update({
                "description": description,
                "company": company,
                "location": location
            })

            enriched.append(job)
            print(f"✅ Enriched: {job['title']}")

        except Exception as e:
            print(f"❌ Failed to enrich {job['title']}: {e}")
            continue

    return enriched


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", type=str, default="")
    parser.add_argument("--location", type=str, default="")
    parser.add_argument("--min_salary", type=int, default=None)
    parser.add_argument("--max_salary", type=int, default=None)
    args = parser.parse_args()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        jobs = fetch_jobs(driver, max_jobs=20)

        if jobs:
            enriched = enrich_jobs(driver, jobs)

            with open("../data/seek_jobs_enriched.json", "w", encoding="utf-8") as f:
                json.dump(enriched, f, indent=2)

            print(f"\n✅ Enriched and saved {len(enriched)} jobs to ../data/seek_jobs_enriched.json")
        else:
            print("⚠️ No jobs collected to enrich.")
    finally:
        driver.quit()
