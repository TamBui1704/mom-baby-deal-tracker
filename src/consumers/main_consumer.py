import json
import os
import psycopg2
import requests
import concurrent.futures
from confluent_kafka import Consumer, KafkaError
from datetime import datetime

# Load configuration from environment variables
# All environment-specific variables must be defined in .env
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')

# Business logic constants (Less likely to change)
PRICE_ALERT_THRESHOLD = 300000 

# --- Task A: Alert (Telegram) ---
def task_alert_telegram(data):
    if data.get('type') == 'DATA' and data['sale_price'] < PRICE_ALERT_THRESHOLD:
        msg = f"🚨 DEAL HOT: {data['product_name']}\n🔖 Brand: {data.get('brand', 'No Brand')}\n💰 Giá: {data['sale_price']:,}đ\n🔗 Link: {data.get('product_link', 'No Link')}\n⏰ Lúc: {data['scraped_at']}"
        
        # Chỉ gửi nếu có Token
        if not TELEGRAM_TOKEN:
            print(f" [A] Alert skipped (No TELEGRAM_BOT_TOKEN): {msg.replace(chr(10), ' | ')}")
            return
            
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
            print(f" [A] Alert sent for {data['product_name']}")
        except Exception as e:
            print(f" [A] Telegram error: {e}")

# --- Task B: Data Lake (Backup JSONB) ---
def task_data_lake_backup(data):
    if data.get('type') != 'DATA': return
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO raw.stg_price_events 
            (batch_id, raw_data, product_id, product_name, sale_price, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['batch_id'],
            json.dumps(data),
            data['product_id'],
            data['product_name'],
            data['sale_price'],
            data['scraped_at']
        ))
        conn.commit()
        cur.close()
        conn.close()
        print(f" [B] Data Lake backup completed for ID {data['product_id']}")
    except Exception as e:
        print(f" [B] Data Lake error: {e}")

# --- Task Marker: Xử lý EOF ---
def task_handle_eof(data):
    if data.get('type') != 'EOF': return
    batch_id = data['batch_id']
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO raw.batch_control (batch_id, status)
            VALUES (%s, 'DONE')
            ON CONFLICT (batch_id) DO UPDATE SET status = 'DONE', completed_at = CURRENT_TIMESTAMP;
        """, (batch_id,))
        conn.commit()
        cur.close()
        conn.close()
        print(f" [!!!] EOF Received for {batch_id}. Signal sent to raw.batch_control.")
    except Exception as e:
        print(f" [!!!] EOF Handling error: {e}")

def process_message(msg_value):
    data = json.loads(msg_value)
    
    if data.get('type') == 'EOF':
        task_handle_eof(data)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(task_alert_telegram, data)
            executor.submit(task_data_lake_backup, data)

def run_consumer():
    topic = 'price_raw' # Fixed internal topic name
    
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'price-processor-group',
        'auto.offset.reset': 'earliest'
    }
    
    import time
    
    max_retries = 30
    retry_delay = 5
    connected = False
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to Kafka at {KAFKA_BOOTSTRAP_SERVERS} (Attempt {attempt + 1}/{max_retries})...")
            consumer = Consumer(conf)
            # A simple metadata request to check connection
            consumer.list_topics(timeout=5)
            connected = True
            print("Successfully connected to Kafka broker!")
            break
        except KafkaError as e:
            print(f"Failed to connect to Kafka broker: {e}")
        except Exception as e:
            print(f"Error during Kafka connection attempt: {e}")
        
        print(f"Retrying in {retry_delay} seconds...")
        time.sleep(retry_delay)

    if not connected:
        print("Failed to connect to Kafka after maximum retries. Exiting.")
        return

    consumer.subscribe([topic])
    
    print(f"Stream Processor started. Listening on {topic}...")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            process_message(msg.value().decode('utf-8'))
            
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    run_consumer()
