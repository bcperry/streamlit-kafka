#!/usr/bin/env python
import os
import json
import time
import psycopg2
from psycopg2.extras import execute_values
from confluent_kafka import Consumer
from dotenv import load_dotenv

load_dotenv(".env")

def create_database_connection():
    """Create a connection to the PostgreSQL database."""
    conn = None
    retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(retries):
        try:
            print(f"Connecting to PostgreSQL database (attempt {attempt+1}/{retries})...")
            conn = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "postgres"),
                port=os.environ.get("POSTGRES_PORT", "5432"),
                database=os.environ.get("POSTGRES_DB", "sensordata"),
                user=os.environ.get("POSTGRES_USER", "postgres"),
                password=os.environ.get("POSTGRES_PASSWORD", "postgres")
            )
            print("Successfully connected to PostgreSQL database")
            break
        except psycopg2.OperationalError as e:
            print(f"Connection failed (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Could not connect to database.")
                raise
    
    return conn

def create_tables(conn):
    """Create tables if they don't exist."""
    with conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(50) NOT NULL,
            temperature NUMERIC(5,2) NOT NULL,
            humidity NUMERIC(5,2) NOT NULL,
            pressure NUMERIC(7,2) NOT NULL,
            timestamp NUMERIC(18,6) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_sensor_data_device_id ON sensor_data(device_id);
        CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data(timestamp);
        """)
        conn.commit()
        print("Tables created/verified in PostgreSQL")

def insert_sensor_data(conn, data_batch):
    """Insert multiple sensor data records into PostgreSQL."""
    if not data_batch:
        return
    
    with conn.cursor() as cur:
        insert_query = """
        INSERT INTO sensor_data 
        (device_id, temperature, humidity, pressure, timestamp)
        VALUES %s
        """
        
        # Format data for execute_values
        values = [
            (
                item["device_id"],
                item["temperature"],
                item["humidity"],
                item["pressure"],
                item["timestamp"]
            )
            for item in data_batch
        ]
        
        execute_values(cur, insert_query, values)
        conn.commit()
        print(f"Inserted {len(data_batch)} records into PostgreSQL")

def create_kafka_consumer():
    """Create and return a Kafka consumer."""
    config = {
        'bootstrap.servers': os.environ.get("KAFKA_BROKER"),
        'group.id': 'postgres-sink-consumer',
        'auto.offset.reset': 'earliest',
        'session.timeout.ms': 30000,
        'heartbeat.interval.ms': 10000
    }
    
    print(f"Connecting to Kafka broker: {os.environ.get('KAFKA_BROKER')}")
    
    consumer = Consumer(config)
    
    # Subscribe to the topic from environment variables
    topic_name = os.environ.get("TOPIC", "sensor-data")
    print(f"Subscribing to topic: {topic_name}")
    consumer.subscribe([topic_name])
    
    return consumer

def main():
    """Main function for the Kafka to PostgreSQL connector."""
    print("Starting Kafka to PostgreSQL connector...")
    
    # Connect to PostgreSQL
    conn = create_database_connection()
    
    # Create tables if they don't exist
    create_tables(conn)
    
    # Create Kafka consumer
    consumer = create_kafka_consumer()
    
    # Configuration for batch processing
    batch_size = int(os.environ.get("BATCH_SIZE", "10"))
    max_poll_interval = float(os.environ.get("MAX_POLL_INTERVAL", "1.0"))
    
    # Variables for batch processing
    data_batch = []
    last_commit_time = time.time()
    
    try:
        while True:
            msg = consumer.poll(max_poll_interval)
            
            if msg is None:
                # If we have data in the batch and a certain time has passed, process it
                if data_batch and (time.time() - last_commit_time > 5.0):
                    insert_sensor_data(conn, data_batch)
                    data_batch = []
                    last_commit_time = time.time()
                continue
            
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            try:
                # Parse message value
                value = json.loads(msg.value().decode('utf-8'))
                data_batch.append(value)
                
                # If batch size is reached, insert into database
                if len(data_batch) >= batch_size:
                    insert_sensor_data(conn, data_batch)
                    data_batch = []
                    last_commit_time = time.time()
                
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
            except Exception as e:
                print(f"Error processing message: {e}")
    
    except KeyboardInterrupt:
        print("Interrupting gracefully...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Insert any remaining data
        if data_batch:
            try:
                insert_sensor_data(conn, data_batch)
            except Exception as e:
                print(f"Error inserting final batch: {e}")
        
        # Close connections
        if conn and not conn.closed:
            conn.close()
            print("PostgreSQL connection closed")
        
        consumer.close()
        print("Kafka consumer closed")
        print("Connector shutdown complete")

if __name__ == "__main__":
    main()
