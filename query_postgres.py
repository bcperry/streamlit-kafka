#!/usr/bin/env python
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import pandas as pd
from prettytable import PrettyTable

load_dotenv(".env")

def connect_to_postgres():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            database=os.environ.get("POSTGRES_DB", "sensordata"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", "postgres")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)

def show_table_info():
    """Display information about the sensor_data table."""
    conn = connect_to_postgres()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM sensor_data;")
        count = cur.fetchone()[0]
        
        print(f"Total records in sensor_data table: {count}")
        
        # Show the table schema
        cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = 'sensor_data';
        """)
        
        columns = cur.fetchall()
        table = PrettyTable()
        table.field_names = ["Column Name", "Data Type", "Max Length"]
        for col in columns:
            table.add_row([col[0], col[1], col[2] if col[2] else "N/A"])
        
        print("\nTable Schema:")
        print(table)
    
    conn.close()

def query_latest_records(limit=10):
    """Query the latest records from the sensor_data table."""
    conn = connect_to_postgres()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
        SELECT 
            id, 
            device_id, 
            temperature, 
            humidity, 
            pressure, 
            timestamp,
            to_timestamp(timestamp) as datetime,
            created_at
        FROM sensor_data
        ORDER BY timestamp DESC
        LIMIT %s;
        """, (limit,))
        
        records = cur.fetchall()
        
        if not records:
            print("No records found in the database.")
            return
        
        # Convert to pandas DataFrame for better display
        df = pd.DataFrame(records)
        
        print(f"\nLatest {limit} Records:")
        print(df)
    
    conn.close()

def query_device_stats():
    """Query statistics by device_id."""
    conn = connect_to_postgres()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
        SELECT 
            device_id,
            COUNT(*) as record_count,
            MIN(temperature) as min_temp,
            MAX(temperature) as max_temp,
            AVG(temperature) as avg_temp,
            MIN(humidity) as min_humidity,
            MAX(humidity) as max_humidity,
            AVG(humidity) as avg_humidity,
            MIN(pressure) as min_pressure,
            MAX(pressure) as max_pressure,
            AVG(pressure) as avg_pressure,
            MIN(to_timestamp(timestamp)) as first_record_time,
            MAX(to_timestamp(timestamp)) as last_record_time
        FROM sensor_data
        GROUP BY device_id
        ORDER BY device_id;
        """)
        
        stats = cur.fetchall()
        
        if not stats:
            print("No records found in the database.")
            return
        
        # Convert to pandas DataFrame for better display
        df = pd.DataFrame(stats)
        
        print("\nStatistics by Device:")
        print(df)
    
    conn.close()

def main():
    """Main function."""
    print("PostgreSQL Database Query Tool")
    print("=============================")
    
    show_table_info()
    query_latest_records()
    query_device_stats()

if __name__ == "__main__":
    main()
