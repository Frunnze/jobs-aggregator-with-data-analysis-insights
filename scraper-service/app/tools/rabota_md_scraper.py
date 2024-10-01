from bs4 import BeautifulSoup as bs4
import requests
from collections import Counter
import re
from unidecode import unidecode


it_skills = [
    'net', 'sql', 'nosql', 'js', 'python', 'nestjs', 'node', 'nodejs', 
    'restful', 'java', 'javascript', 'c#', 'c++', 'ruby', 'php', 'swift', 
    'go', 'kotlin', 'r', 'typescript', 'rust', 'perl', 'scala', 'django', 
    'flask', 'express.js', 'ruby on rails', 'spring', 'asp.net', 'angular', 
    'react', 'vue.js', 'laravel', 'svelte', 'jquery', 'bootstrap', 'c'
    'materialize', 'tailwind', 'css' 'react native', 'flutter', 'xamarin', 
    'ionic', 'pandas', 'numpy', 'scikitlearn', 'tensorflow', 'keras', 
    'pytorch', 'matplotlib', 'seaborn', 'nltk', 'opencv', 'mysql', 
    'postgresql', 'mongodb', 'sqlite', 'oracle', 'microsoft sql server', 
    'redis', 'cassandra', 'aws', 'azure', 'google cloud platform', 'heroku', 
    'digitalocean', 'docker', 'kubernetes', 'jenkins', 'git', 'ansible', 
    'terraform', 'ci/cd', 'penetration testing', 'ethical hacking', 
    'firewall configuration', 'network security', 'malware analysis', 
    'tcp/ip', 'dns', 'lan/wan', 'vpn', 'voip', 'git', 'subversion (svn)', 
    'mercurial', 'agile', 'scrum', 'kanban', 'waterfall', 'jira', 'trello', 
    'asana', 'microsoft project', 'api development', 'web scraping', 
    'ui/ux design', 'machine learning', 'nlp', 'blockchain', 'iot'
]


class RabotaMdScraper:
    def __init__(self) -> None:
        pass

    def extract_page_links(self, url):
        web_page = requests.get(url)
        soup = bs4(web_page.text, "html.parser")

        # Access the page container with the jobs
        jobs_page_container = soup.find(
            "div", 
            class_="b_info10 vacancy-list space-y-5"
        )
        
        # Get all the jobs into a list
        jobs_containers = jobs_page_container.find_all(
            "div", 
            class_="vacancyCardItem previewCard"
        )

        # Get the page link of each job
        jobs_pages_links = []
        for job in jobs_containers:
            job_page_link = "https://www.rabota.md" + job.find("a").get("href")
            jobs_pages_links.append(job_page_link)

        return jobs_pages_links
    
    def find_currency_and_price(self, text):
        text = text.replace(" ", "").replace("\n", "")
        # Regular expression pattern to match currency and prices
        pattern = r'(?P<currency>\$|€|euro|mdl|usd)?\s*(?P<price>[0-9]+(?:\.[0-9]{1,2})?)\s*(?P<currency2>\$|€|euro|mdl|usd)?'
        
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
        currency, salary = self.find_currency_and_price(text_to_analyze)
        if currency and salary:
            job_data["salary"] = salary
            job_data["currency"] = currency

        words = re.findall(r'\w+(?:[\+\#]\w*)*', text_to_analyze)
        temp_words = []
        for word in words:
            if word in it_skills:
                temp_words.append(word)
        words = temp_words

        job_data["skills"] = dict(Counter(words))
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
    RabotaMdScraper().scrape()