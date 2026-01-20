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
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


from urllib.parse import quote_plus

import time

start = time.time()


def build_url(keywords="", location="", min_salary=None, max_salary=None, page=1, region="Australia"):
    base_url = "https://www.seek.com.au" if region == "Australia" else "https://www.seek.co.nz"
    keyword_slug = "-".join(keywords.lower().split())
    location_slug = location.replace(" ", "-")

    url = f"{base_url}/{keyword_slug}-jobs/in-{location_slug}"
    min_part = "" if min_salary is None else min_salary
    max_part = "" if max_salary is None else max_salary
    url += f"?page={page}&salaryrange={min_part}-{max_part}&salarytype=annual&sortmode=ListedDate"
    return url



def fetch_jobs(driver, max_jobs=20):
    jobs = []
    page = 1
    fetch_start = None
    while len(jobs) < max_jobs:
        fetch_start = time.time()
        url = build_url(args.keywords, args.location, args.min_salary, args.max_salary, page, args.region)
        print(f"Visiting {url}")

        
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        #time.sleep(10)



        # 🔍 Dump the HTML of the first page for inspection
        if page == 1:
            debug_path = Path(__file__).resolve().parent.parent / "seek_debug_page1.html"
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)

        # Wait until job titles are visible
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-automation='jobTitle']"))
            )
            print("Job cards are now visible.")
        except TimeoutException:
            print("Job titles not loaded after waiting.")
            return []


        job_elements = driver.find_elements(By.CSS_SELECTOR, "a[data-automation='jobTitle']")

        for title_elem in job_elements:
            if len(jobs) >= max_jobs:
                break
            try:
                title = title_elem.text
                link = title_elem.get_attribute("href")

                jobs.append({
                    "title": title,
                    "link": link
                })
            except Exception as e:
                print("Skipping job due to:", e)

        print("Time to fetch job ", len(jobs), ":", time.time() - fetch_start, "s")

        if len(jobs) >= max_jobs:
            break

        page += 1
        time.sleep(2)

    return jobs


def enrich_single_job(job):
    local_driver = webdriver.Chrome(options=chrome_options)
    local_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    result = {}

    try:
        enrich_start = time.time()

        local_driver.get(job["link"])
        WebDriverWait(local_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation='jobAdDetails']"))
        )

        result.update(job)
        result["description"] = local_driver.find_element(By.CSS_SELECTOR, "div[data-automation='jobAdDetails']").text
        result["company"] = local_driver.find_element(By.CSS_SELECTOR, "[data-automation='advertiser-name']").text
        result["location"] = local_driver.find_element(By.CSS_SELECTOR, "[data-automation='job-detail-location']").text
        try:
            result["date_posted"] = local_driver.find_element(By.CSS_SELECTOR, 'span[data-automation="jobListingDate"]').text
        except:
            result["date_posted"] = "N/A"
        print("Time to enrich job - ", job['title'], ": started at (offset) ",  time.time() - start, ", runtime ", time.time() - enrich_start, "s")

    except Exception as e:
        print(f"❌ Error on job: {job['title']} — {e}")
    finally:
        local_driver.quit()

    return result

def enrich_jobs_parallel(jobs, max_threads=5):
    enriched = []
    with ThreadPoolExecutor(max_threads) as executor:
        futures = {executor.submit(enrich_single_job, job): job for job in jobs}
        for i, future in enumerate(as_completed(futures)):
            enriched_job = future.result()
            if enriched_job:
                enriched.append(enriched_job)
            print(f"Enriched job {i+1}/{len(jobs)}")
    return enriched


def enrich_jobs(driver, jobs):
    print(f"\nVisiting {len(jobs)} job detail pages to extract more info...\n")
    enrich_start = None
    enriched = []

    for job in jobs:
        enrich_start = time.time()

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

            try:
                date_element = driver.find_element(By.CSS_SELECTOR, 'span[data-automation="jobListingDate"]')
                date_posted = date_element.text  # e.g., "Posted 3 days ago"
            except Exception as e:
                date_posted = 'N/A'


            job.update({
                "description": description,
                "company": company,
                "location": location,
                "date_posted": date_posted
            })

            enriched.append(job)
            print(f"Enriched: {job['title']}")

        except Exception as e:
            print(f"Failed to enrich {job['title']}: {e}")
            continue
        
        print("Time to enrich job ", len(enriched), ":", time.time() - enrich_start, "s")

    return enriched


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", type=str, default="data scientist")
    parser.add_argument("--location", type=str, default="Melbourne VIC")
    parser.add_argument("--min_salary", type=int, default=100000)
    parser.add_argument("--max_salary", type=int, default=None)
    parser.add_argument("--threads", type=int, default=5)
    parser.add_argument("--region", type=str, default="Australia", choices=["Australia", "New Zealand"])
    parser.add_argument("--max_jobs", type=int, default=20)



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
        jobs = fetch_jobs(driver, max_jobs=args.max_jobs)

        if jobs:
            if args.threads<=1:
                enriched = enrich_jobs(driver, jobs)
            else:
                enriched = enrich_jobs_parallel(jobs, args.threads)
                
            with open("../data/seek_jobs_enriched.json", "w", encoding="utf-8") as f:
                json.dump(enriched, f, indent=2)

            print(f"\nEnriched and saved {len(enriched)} jobs to ../data/seek_jobs_enriched.json")
        else:
            print("No jobs collected to enrich.")
    finally:
        driver.quit() 
        
    print("Total runtime:", time.time() - start, "s")
