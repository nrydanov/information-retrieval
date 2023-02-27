import requests
from bs4 import BeautifulSoup
import json
import re
from threading import Thread
from requests.exceptions import MissingSchema, InvalidSchema
from urllib.parse import unquote

BASE_DIR = 'content'

class Scraper:
  
  all_words = set()
  
  def __init__(self, start_url, base_url, dest):
    self.processed = set()
    self.start_url = start_url
    self.base_url = base_url
    self.dest = dest

  def get_page(self, soup):
    for el in soup.find_all('a'):
      link = el.get('href')
      if link == None:
        continue
    
      if link.find(self.base_url) != -1 and link not in self.processed and link.find("?") == -1:
        self.processed.add(link)
        yield link
        
  def update_dict(self, body):
    
    for el in set(body.split(' ')):
      self.all_words.add(re.sub('[^А-Яа-я0-9]+', '', el))

  def process_text(self, soup):
      
    text = list(map(lambda x: x.getText(), soup.find_all('p')))
    
    body = "\n".join(text)
    return body
  
  def save_result(self, content):
    if self.dest == 'file':
      output = re.sub(" +", " ", re.sub('\W+', ' ', content['title']))
      try:
        f = open(f"{BASE_DIR}/{output}.json", 'w')
      except:
        print("Can't open file\n")
        return
      f.write(json.dumps(content, ensure_ascii=False, indent=2))
    elif self.dest == 'engine':
      requests.post("http://localhost:8081/engine", json={"documents" : [content]})
    else:
      raise ValueError("Invalid destination")
    
  def process_request(self, soup, url):
    body = self.process_text(soup)
    
    self.update_dict(body)
    
    if soup.title.text.find("|") > 0:
      title = soup.title.text.split('|')[0][:-1]
    else:
      title = soup.title.text
      
    categories = list(map(lambda x: x['data-name'], 
                    soup.find_all('li', {'class': 'category normal'})))
    
    content = {'title': title, 
               'body': body, 
               'categories': categories,
               'url': url}
    
    self.save_result(content)

  def scrap_page(self, url):
    try:
      response = requests.get(url)
    except (MissingSchema, InvalidSchema):
      print("Wrong URL is found, skipping...")
      return
    print(f"Scrapping {unquote(url)}")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    _ = Thread(target=self.process_request, args=(soup, url)).run()
    
    for page in self.get_page(soup):
        self.scrap_page(page)
        
  def start(self):
    try:
      self.scrap_page(self.start_url)
    except KeyboardInterrupt:
      pass
    
    f = open("dict.txt", "w")
    f.write("\n".join(self.all_words))
    f.close()
   
url = "https://wowwiki.fandom.com/ru/wiki/Служебная:Все_страницы"
base_url = "https://wowwiki.fandom.com/ru/wiki/"
scraper = Scraper(url, base_url, "engine")

scraper.start()
