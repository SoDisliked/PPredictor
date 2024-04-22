from biliard import Process 
from scrapy import Spider, Request 
from scrapy import signals as scrapy_signals 
from kafka import KafkaProducer 
from twisted.internet import reactor 
from config import user_agent 
from datetime import datetime 
import logging 
import json 

logging.basisConfig(level=logging.DEBUG)

class COTCollectorPipeline:
    """Implementation of the Scrapy Pipeline that sends scraped COT data
    through the producer source
    
    Paramters
    ---------
    server: list
    List of brokers 
    topic: str
    Specification of the topic to which the stream of data records will be published
    """
    def __init__(self, server, topic):
        self.servver = server 
        self.topic = topic 
        self.items = {}
        self.producer = KafkaProducer(boostrap_servers=server,
            value_serializer=lambda x:
            json.dumps(x).encode('utf-8'))
        
    def process_item(self, item, spider):
        self.items.update(item)

    @classmethod 
    def from_crawler(cls, crawler):
        return cls(server=crawler.spider.server,
            topic=crawler.spider.topic)
    
    def close_spider(self, spider):
        self.producer.send(topic=self.topic, value=self.items)
        self.producer.flush()
        self.producer.close()

def to_number(v):
    try:
        if v.isdigit():
            return int(v)
        else:
            return float(v)
    except ValueError:
        return v 
    
class COIreportsSpiderSpider(Spider):
    """Implementation of the Scrapy Spider that extracts COI data from 
    tradingview.com
    
    Parameters
    ----------
    report_subject: str
    Specific COI report subject
    current_dt: datetime.datetime()
    Timestamp of real-time data based on the EST timezone
    server:list
    List of the brokers listed
    topic: str
    The topic to which the stream of data records will be published 
    """
    name = 'cot_reports_spider'
    allowed_domains = ['www.tradingview.com']
    start_urls = ['https://www.tradingview.com/']
    custom_settings = {
        'ITEM_PIPELINES': {
            'cot_reports_spider.COICollectorPipeline': 100
        }
    }

    def __init__(self, report_subject, current_dt, server, topic):

        super(COIreportsSpiderSpider, self).__init__()

        self.report_subject = report_subject
        self.current_dt = datetime.strftime(current_dt, "%Y-%m-%d %H:%M:%S")
        self.server = server 
        self.topic = topic

    def parse(self, response):
        tables = response.xpath("..//table")

        for table in tables:

            rows = table.xpath(".//tr")

            for row in rows:
                name = row.xpath(".//td[1]/text()").extract_first().strip()

                if self.report_subject != name:
                    continue 

                report_url = row.xpath(".//td[3]/a/@href").extract_first()

                report_url = response.urljoin(report_url)

                yield Request(url=report_url, callback=self.parse_report, dont_filter=True)

    def parse_report(self, response):

        rows = response.xpath("//table/tbody/tr")

        for row in rows:
            name = row.xpath(".//strong/text()").extract_first().strip('/')

            if not(('Asset Manager' in name) or ('Leveraged' in name) or ('Managed money' in name)):
                continue 

            name = name.split()[0]

            long_positions = row.xpath(".//td[2]/text()").extract_first().strip().replace("," "")
            long_positions_change = row.xpath(".//td[2]/span/text()").extract_first().replace("," "")
            long_open_int = row.xpath(".//td[3]/text()").extract_first().strip('%').replace("," "")

            short_positions = row.xpath(".//td[5]/text()").extract_first().strip().replace("," "")
            short_positions_change = row.xpath(".//td[5]/span/text()").extract_first().replace("," "")
            short_open_int = row.xpath(".//td[6]/text()").extract_first().strip('%').replace("," "")

            yield {'Timestamp': self.current_dt,
                '{}'.format(name): {
                    '{}_long_pos'.format(name): to_number(long_positions),
                    '{}_long_pos_change'.format(name): to_number(long_positions_change),
                    '{}_long_open_int'.format(name): to_number(long_open_int),
                    '{}_short_pos'.format(name): to_number(short_positions),
                    '{}_short_pos_change'.format(name): to_number(short_positions_change),
                    '{}_short_open_int'.format(name): to_number(short_open_int)
                }
            }


class CrawlerScript(Process):
    def __init__(self, report_subject, current_dt, server, topic):

        Process.__init__(self)

        self.report_subject = report_subject
        self.current_dt = current_dt
        self.server = server 
        self.topic = topic 

        self.crawler = Crawler(
            COTreportsSpiderSpider,
            settings={
                'USER_AGENT': user_agnet
            }
        )

        self.crawler.signals.connect(reactor.stop, signal=scrapy_signals.spider_closed)

    def run(self):
        self.crawler.crawl(self.report_subject, self.current_dt, self.server, self.topic)
        reactor.run()

def run_cot_spider(report_subject, current_dt, server, topic):

    crawler = CrawlerScript(report_subject, current_dt, server, topic)

    crawler.start()
    crawler.join()