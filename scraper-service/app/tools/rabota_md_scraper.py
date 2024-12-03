from bs4 import BeautifulSoup as bs4
import requests
import re
from unidecode import unidecode
import demjson3

from ..models import SkillsList


extracted_skills = SkillsList.query.all()
it_skills2 = [demjson3.decode(skill.name) for skill in extracted_skills]
print(it_skills2)


class RabotaMdScraper:
    def __init__(self) -> None:
        pass

    def extract_page_links(self, url):
        web_page = requests.get(url)
        print("response", web_page.status_code)
        soup = bs4(web_page.text, "html.parser")

        # Access the page container with the jobs
        jobs_page_container = soup.find(
            "div", 
            class_="b_info10 vacancy-list space-y-5"
        )
        
        # Get all the jobs into a list
        jobs_containers = jobs_page_container.find_all(
            "div", 
            class_="vacancyCardItem previewCard noPaddings"
        )

        # Get the page link of each job
        jobs_pages_links = []
        for job in jobs_containers:
            href = job.find_all("a")[1].get("href")
            if href:
                job_page_link = "https://www.rabota.md" + href
                jobs_pages_links.append(job_page_link)

        return jobs_pages_links
    
    def find_currency_and_price(self, text):
        text = text.replace(" ", "").replace("\n", "")
        # Regular expression pattern to match currency and prices
        pattern = r'(?P<currency>\$|€|euro|eur|mdl|usd)?\s*(?P<price>[0-9]+(?:\.[0-9]{1,2})?)\s*(?P<currency2>\$|€|euro|eur|mdl|usd)?'
        
        # Find all matches in the text
        matches = re.finditer(pattern, text)
        
        # Extracting currency and price from matches
        for match in matches:
            currency1 = match.group('currency')
            price = match.group('price')
            currency2 = match.group('currency2')

            # Determine which currency symbol to use (if any)
            final_currency = currency1 if currency1 else currency2

            if final_currency and price:
                if final_currency == "$": final_currency = "usd"
                if final_currency == "€": final_currency = "euro"
                if final_currency == "eur": final_currency = "euro"
                return final_currency, price
        return None, None
        
    def extract_num(self, num):
        if num:
            nums = re.findall(r'\d+', num)
            if nums:
                return int(nums[0])
        return None
    
    def scrape_page_data(self, link):
        job_data = {}
        web_page = requests.get(link)
        soup = bs4(web_page.text, "html.parser")

        job_data["link"] = link

        job_data_container = soup.find("div", class_="vc_detail")
        top_info = job_data_container.find("div", class_="top-info")

        job_title = top_info.find("h1", class_="mb-5 text-black")
        if job_title: job_data["title"] = job_title.text.strip()

        company_name = top_info.find("span", class_="company-name")
        if company_name: job_data["company_name"] = company_name.text.strip()

        vacancy_id = top_info.find("span", class_="vacancy-id")
        date = vacancy_id.find("span")
        if date: job_data["date"] = date.text.strip()

        summary = job_data_container.find("div", class_="summary")
        summary_divs = summary.find_all("div")
        for div in summary_divs:
            spans = div.find_all("span")
            if len(spans) >= 2 and spans[0].text == "Experiența de munca":
                experience_str = spans[1].text
                experience = self.extract_num(experience_str)
                job_data["experience"] = experience if experience else 0
                break
        
        text_to_analyze = unidecode(job_data_container.text.lower())
        text_to_analyze = text_to_analyze.replace("\n", " ").replace("\t", " ")
        symbols_to_replace = r'[\,\;\?\"\'\:\/\)\(\!]'
        text_to_analyze = re.sub(symbols_to_replace, ' ', text_to_analyze)

        currency, salary = self.find_currency_and_price(text_to_analyze)
        if currency and salary:
            job_data["salary"] = salary
            job_data["currency"] = currency

        job_data["skills"] = {}
        for skill in it_skills2:
            skill_count = 0
            for label in list(skill):
                skill_count += text_to_analyze.count(" " + label + " ")
            if skill_count > 0:
                job_data["skills"][skill[0]] = skill_count

        return job_data

    def scrape(self, first_page=2, max_pages=2, url="https://www.rabota.md/ro/vacancies/category/it/"):
        page = first_page
        data_list = []
        while page <= max_pages:
            jobs_pages_links = self.extract_page_links(url + str(page))
            for link in jobs_pages_links:
                data = self.scrape_page_data(link)
                data_list.append(data)
                print("\n"*5)
                print(data)
            page += 1
        return data_list


if __name__ == "__main__":
    l = RabotaMdScraper().extract_page_links("https://www.rabota.md/ro/vacancies/category/it/2")
    print(l)