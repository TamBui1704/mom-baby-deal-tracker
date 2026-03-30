import json
import time
import os
from datetime import datetime
from confluent_kafka import Producer

# Import scrapers
from core import TikiScraper

# Load configuration from environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
BATCH_ID = os.getenv('BATCH_ID')

class PriceProducer:
    def __init__(self, bootstrap_servers):
        # Initialize Kafka Producer configuration
        self.producer_config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'mom-baby-price-scraper'
        }
        self.producer = Producer(self.producer_config)
        self.scrapers = [TikiScraper()]

    def delivery_report(self, err, msg):
        """ Callback called once for each message produced to indicate delivery result. """
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            pass # Keep logs clean for large batches

    def publish_prices(self, topic, batch_id):
        """ Batch mode: Scrape Mom & Baby products """
        print(f"Starting Scraper Batch {batch_id}... (Target topic: {topic})")
        
        keywords = ["Bỉm Huggies", "Sữa Meiji", "Khăn ướt Moony"]
        messages_sent = 0

        for keyword in keywords:
            for scraper in self.scrapers:
                products = scraper.scrape_keyword(keyword, limit=5)
                for product in products:
                    data = {
                        'type': 'DATA',
                        'batch_id': batch_id,
                        'product_id': product['product_id'],
                        'product_name': product['product_name'],
                        'brand': product.get('brand', 'No Brand'),
                        'unit': product.get('unit', 'Cái'),
                        'pack_quantity': product.get('pack_quantity', 1),
                        'sale_price': product['sale_price'],
                        'product_link': product.get('product_link', ''),
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    self.producer.produce(topic, value=json.dumps(data), callback=self.delivery_report)
                    messages_sent += 1
                    self.producer.poll(0)

        # Gửi tin nhắn EOF Marker để báo hiệu kết thúc Batch
        eof_msg = {
            'type': 'EOF',
            'batch_id': batch_id,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.producer.produce(topic, value=json.dumps(eof_msg), callback=self.delivery_report)
        
        self.producer.flush()
        print(f"Batch {batch_id} completed. Sent {messages_sent} data messages + 1 EOF marker.")

if __name__ == "__main__":
    current_batch_id = BATCH_ID if BATCH_ID else f"real_{int(time.time())}"
        
    PRODUCER = PriceProducer(KAFKA_BOOTSTRAP_SERVERS)
    PRODUCER.publish_prices('price_raw', current_batch_id)
