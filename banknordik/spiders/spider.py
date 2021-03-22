import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import BanknordikItem
from itemloaders.processors import TakeFirst
import requests
import json
pattern = r'(\xa0)?'

url = "https://www.banknordik.dk/api/sdc/news/search"

payload="{{\"page\":{},\"filterType\":\"categories\",\"filterValues\":[]}}"
headers = {
  'authority': 'www.banknordik.dk',
  'pragma': 'no-cache',
  'cache-control': 'no-cache',
  'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
  'accept': 'application/json, text/plain, */*',
  'sec-ch-ua-mobile': '?0',
  'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
  'content-type': 'application/json;charset=UTF-8',
  'origin': 'https://www.banknordik.dk',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://www.banknordik.dk/nyheder',
  'accept-language': 'en-US,en;q=0.9',
  'cookie': 'sdc_device_id=33291755-c879-4a10-0e7b-d384dd7e05fd; ARRAffinity=369d292c28e79ec1b9f03000aacc58d24e97c2cacf25d4dd5cc1077441993fd4; ARRAffinitySameSite=369d292c28e79ec1b9f03000aacc58d24e97c2cacf25d4dd5cc1077441993fd4; TS011c3006=014105db7045632527f478cd71136ade75771638db424ccee73c7672097346ea7d327fe7644cf4f6e47d4c7870b9ae59555222f2f2; TS019c2375=014105db709af1be3d586f5a990846fed831b4122a424ccee73c7672097346ea7d327fe7640af3ac7bc31588498a7ceda452bb4d2be83589b158f1531c527b275ff3fc8de6318823e63686c7739d0c89358ada3147; sdc_auth=eyJwcm9kdWN0cyI6W10sImF2YWlsYWJsZVNlZ21lbnRzIjpbXSwiYXV0aGVudGljYXRlZCI6ZmFsc2V9; CookieInformationConsent=%7B%22website_uuid%22%3A%22a01f6e25-58a1-494f-b264-710ae2cc74b4%22%2C%22timestamp%22%3A%222021-03-22T08%3A18%3A59.778Z%22%2C%22consent_url%22%3A%22https%3A%2F%2Fwww.banknordik.dk%2F%22%2C%22consent_website%22%3A%22banknordik.dk%22%2C%22consent_domain%22%3A%22www.banknordik.dk%22%2C%22user_uid%22%3A%22a1d96b14-8659-45b7-b330-ddd0da58a6b6%22%2C%22consents_approved%22%3A%5B%22cookie_cat_necessary%22%2C%22cookie_cat_functional%22%2C%22cookie_cat_statistic%22%2C%22cookie_cat_marketing%22%2C%22cookie_cat_unclassified%22%5D%2C%22consents_denied%22%3A%5B%5D%2C%22user_agent%22%3A%22Mozilla%2F5.0%20%28Windows%20NT%206.1%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F89.0.4389.90%20Safari%2F537.36%22%7D; _gid=GA1.2.2082452619.1616401140; _fbp=fb.1.1616401140051.125566128; _ga=GA1.2.1920643032.1616401134; _ga_ZWZBZQW4RL=GS1.1.1616401141.1.1.1616401168.0'
}

class BanknordikSpider(scrapy.Spider):
	name = 'banknordik'
	page = 0
	start_urls = ['https://www.banknordik.dk/nyheder']

	def parse(self, response):
		data = requests.request("POST", url, headers=headers, data=payload.format(self.page))
		data = json.loads(data.text)

		for index in range(len(data['results'])):
			links = data['results'][index]['url']
			date = data['results'][index]['date'].split()[0]
			yield response.follow(links, self.parse_post, cb_kwargs=dict(date=date))
		if self.page < data['totalPages']:
			self.page += 1
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response, date):

		title = response.xpath('//h1/text() | //h2/text()').get()
		content = response.xpath('(//div[@class="frame__cell-item"])[position()>2]//text()[not (ancestor::div[@class="frame contact-module contact-module-a"])]').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=BanknordikItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
