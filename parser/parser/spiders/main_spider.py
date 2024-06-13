import scrapy
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class MySpider(scrapy.Spider):
    name = 'main'
    start_urls = ['https://kazan.cian.ru/cat.php?deal_type=sale&engine_version=2&offer_type=flat&p=1&region=4777&room1=1']
    handle_httpstatus_list = [403, 404, 500]
    page_number = 1

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        for url in self.start_urls:
            yield scrapy.Request(url, headers=headers, callback=self.parse, errback=self.errback_httpbin, dont_filter=True)

    def parse(self, response):
        if response.status == 200:
            posts = response.xpath(
                "//div[@id='frontend-serp']//div[contains(@class, '_93444fe79c--serp--bTAO_') and contains(@class, '_93444fe79c--serp--light--moDYM')]//div[contains(@class, '_93444fe79c--wrapper--W0WqH')]//div[contains(@class, '_93444fe79c--container--kZeLu') and contains(@class, '_93444fe79c--link--DqDOy')]"
            )

            for post in posts:
                link = post.xpath(".//a[contains(@class, '_93444fe79c--link--eoxce')]/@href").get()

                # Извлекаем текст из вложенного элемента <span>
                span_text = post.xpath(".//a[contains(@class, '_93444fe79c--link--eoxce')]/span//text()").get()

                print(f'Link: {link}, Span: {span_text}')

            self.page_number += 1
            parsed_url = urlparse(response.url)
            query_params = parse_qs(parsed_url.query)
            query_params['p'] = [str(self.page_number)]
            new_query_string = urlencode(query_params, doseq=True)
            next_page = urlunparse(parsed_url._replace(query=new_query_string))

            yield scrapy.Request(next_page, headers=response.request.headers, callback=self.parse)
        else:
            self.logger.error(f'HTTP status code {response.status} is not handled or not allowed')

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f'HttpError on {response.url}')

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error(f'DNSLookupError on {request.url}')

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error(f'TimeoutError on {request.url}')
