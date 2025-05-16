#!/usr/bin/env python
import json
import socket
import os
import math
from random import choice
import time
from confluent_kafka import Producer
from dotenv import load_dotenv
import random

load_dotenv(".env")
print(os.environ.get("TOPIC"))

class IoTDevice:
    def __init__(self, device_id, refresh_rate):
        self.device_id = device_id
        self.refresh_rate = refresh_rate
        # Device characteristics - each device has slightly different baseline readings
        self.base_temp = random.uniform(21.0, 23.0)  # Base temperature in Celsius
        self.base_humidity = random.uniform(40.0, 60.0)  # Base humidity percentage
        self.base_pressure = random.uniform(1000.0, 1020.0)  # Base pressure in hPa
        
        # Environment simulation
        self.time_of_day = 0  # 0-24 hour cycle
        self.season = 0  # 0-4 season cycle (0=winter, 1=spring, 2=summer, 3=fall)
        self.daily_drift = random.uniform(-0.5, 0.5)  # Daily drift in readings
        
        # Failure modes that can develop over time
        self.temp_sensor_drift = 0  # Temperature sensor drift
        self.humidity_sensor_fault = 0  # Humidity sensor degradation
        self.pressure_sensor_spike_chance = 0.001  # Chance of pressure sensor spikes
        
        # Correlation parameters (realistic physics)
        # Temperature and humidity are inversely correlated
        # Pressure changes can affect both temperature and humidity

    def update_environmental_factors(self):
        """Update time-based environmental factors"""
        # Update time of day (0-24 hour cycle)
        self.time_of_day = (self.time_of_day + 0.1) % 24
        
        # Slowly update season (0-4 cycle, complete cycle every ~1000 readings)
        self.season = (self.season + 0.001) % 4
        
        # Gradually increase sensor drift/degradation over time
        if random.random() < 0.001:  # Very small chance of sensor drift increasing
            self.temp_sensor_drift += random.uniform(0, 0.1)
        
        if random.random() < 0.0005:  # Even smaller chance of humidity sensor fault
            self.humidity_sensor_fault += random.uniform(0, 0.05)

    def generate_data(self):
        """Generate realistic sensor data with natural correlations"""
        self.update_environmental_factors()
        
        # Calculate time-of-day effect (diurnal cycle)
        # Peak temperature at 14:00, lowest at 2:00
        time_factor = math.sin((self.time_of_day - 2) * math.pi / 12)
        
        # Calculate seasonal effect
        # Summer = hotter, winter = colder
        seasonal_temp_factor = math.sin(self.season * math.pi / 2)
        
        # Base temperature with natural variations
        temperature = (self.base_temp + 
                     3 * seasonal_temp_factor + 
                     2 * time_factor + 
                     self.daily_drift + 
                     self.temp_sensor_drift + 
                     random.normalvariate(0, 0.3))  # Small random noise
        
        # Humidity is inversely correlated with temperature, with some randomness
        # Higher temps = lower humidity
        humidity_factor = -0.3 * (temperature - self.base_temp)
        humidity = (self.base_humidity + 
                  humidity_factor + 
                  10 * math.sin(self.time_of_day * math.pi / 12) + 
                  random.normalvariate(0, 2))  # Random variations
                  
        # Apply humidity sensor fault if present
        if self.humidity_sensor_fault > 0:
            humidity *= (1 - self.humidity_sensor_fault)
        
        # Pressure varies less but has some correlation with weather patterns
        pressure = (self.base_pressure + 
                  2 * math.sin(self.season * math.pi * 2) + 
                  random.normalvariate(0, 0.5))  # Random variations
                  
        # Ensure values are within realistic bounds and rounded properly
        temperature = round(max(min(temperature, 35.0), 10.0), 2)
        humidity = round(max(min(humidity, 95.0), 20.0), 2)
        pressure = round(max(min(pressure, 1040.0), 970.0), 2)
        
        return {
            "device_id": self.device_id,
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure,
            "timestamp": time.time()
        }

    def introduce_anomaly(self):
        """Introduce realistic anomalies in the data with meaningful correlations"""
        # Get baseline normal data first
        data = self.generate_data()
        
        # Choose anomaly type with different probabilities
        anomaly_type = random.choices(
            ['temperature_spike', 'temperature_drop', 'humidity_spike', 
             'humidity_drop', 'pressure_spike', 'pressure_drop', 
             'sensor_failure', 'correlated_failure'],
            weights=[20, 15, 15, 15, 10, 10, 10, 5],  # Different probabilities for different anomalies
            k=1
        )[0]
        
        # Mark that this is an anomaly
        data["anomaly"] = anomaly_type
        
        if anomaly_type == 'temperature_spike':
            # Sudden temperature increase (e.g., fire, equipment malfunction)
            data["temperature"] = round(data["temperature"] + random.uniform(15.0, 25.0), 2)
            # Humidity decreases with high temperature
            data["humidity"] = round(max(data["humidity"] * 0.7, 15.0), 2)
            
        elif anomaly_type == 'temperature_drop':
            # Sudden temperature drop (e.g., AC malfunction, door left open in cold weather)
            data["temperature"] = round(data["temperature"] - random.uniform(10.0, 15.0), 2)
            # Humidity might increase with temperature drop
            data["humidity"] = round(min(data["humidity"] * 1.3, 95.0), 2)
            
        elif anomaly_type == 'humidity_spike':
            # Sudden humidity increase (e.g., water leak, steam)
            data["humidity"] = round(min(data["humidity"] + random.uniform(25.0, 35.0), 99.0), 2)
            # Temperature might be slightly affected
            data["temperature"] = round(data["temperature"] * 0.95, 2)
            
        elif anomaly_type == 'humidity_drop':
            # Sudden humidity drop (e.g., heating system, dehumidifier malfunction)
            data["humidity"] = round(max(data["humidity"] - random.uniform(20.0, 30.0), 5.0), 2)
            # Temperature might rise slightly with very dry air
            data["temperature"] = round(data["temperature"] * 1.05, 2)
            
        elif anomaly_type == 'pressure_spike':
            # Sudden pressure increase (e.g., air system malfunction)
            data["pressure"] = round(data["pressure"] + random.uniform(50.0, 100.0), 2)
            
        elif anomaly_type == 'pressure_drop':
            # Sudden pressure drop (e.g., air leak, ventilation issue)
            data["pressure"] = round(data["pressure"] - random.uniform(50.0, 80.0), 2)
            
        elif anomaly_type == 'sensor_failure':
            # Complete sensor failure (reads fixed value, zero, or NaN)
            failed_sensor = random.choice(['temperature', 'humidity', 'pressure'])
            failure_mode = random.choice(['zero', 'fixed', 'extreme'])
            
            if failure_mode == 'zero':
                data[failed_sensor] = 0.0
            elif failure_mode == 'fixed':
                # Stuck reading
                pass  # Already using the last reading
            else:  # extreme
                if failed_sensor == 'temperature':
                    data[failed_sensor] = round(random.uniform(80.0, 120.0), 2)
                elif failed_sensor == 'humidity':
                    data[failed_sensor] = round(random.uniform(0.1, 3.0), 2)
                else:  # pressure
                    data[failed_sensor] = round(random.uniform(1200.0, 1500.0), 2)
            
            data["anomaly"] = f"{failed_sensor}_{failure_mode}"
            
        elif anomaly_type == 'correlated_failure':
            # Multiple sensors showing anomalous readings together
            # Example: Heating system failure affects temperature and humidity
            data["temperature"] = round(data["temperature"] + random.uniform(18.0, 30.0), 2)
            data["humidity"] = round(max(data["humidity"] * 0.5, 10.0), 2)
            data["pressure"] = round(data["pressure"] + random.uniform(15.0, 30.0), 2)
            data["anomaly"] = "multi_sensor_failure"
        
        return data
            
    def emulate(self):
        """Generate sensor data, occasionally introducing anomalies"""
        # Gradually increasing chance of anomalies over time (aging equipment)
        anomaly_chance = 0.05 + min(0.15, self.temp_sensor_drift + self.humidity_sensor_fault)
        
        # Introduce cluster of anomalies occasionally to simulate systemic issues
        if hasattr(self, 'in_anomaly_cluster') and self.in_anomaly_cluster > 0:
            data = self.introduce_anomaly()
            self.in_anomaly_cluster -= 1
        elif random.random() < anomaly_chance:
            # Start a potential cluster of anomalies
            if random.random() < 0.3:  # 30% chance of clustered anomalies
                self.in_anomaly_cluster = random.randint(3, 8)  # Cluster of 3-8 anomalies
                data = self.introduce_anomaly()
                self.in_anomaly_cluster -= 1
            else:
                data = self.introduce_anomaly()
        else:
            data = self.generate_data()
        
        # Print to stdout for visibility
        print(json.dumps(data))

        return json.dumps(data)
            


if __name__ == '__main__':
    # Wait for Kafka to become available in Docker environment
    if os.environ.get("KAFKA_BROKER", "").startswith("kafka:"):
        print("Running in Docker environment, waiting for Kafka to start...")
        
        kafka_host = os.environ.get("KAFKA_BROKER").split(":")[0]
        kafka_port = int(os.environ.get("KAFKA_BROKER").split(":")[1])
        
        max_attempts = 20
        attempt = 0
        connected = False
        
        while not connected and attempt < max_attempts:
            attempt += 1
            try:
                print(f"Attempt {attempt}/{max_attempts}: Connecting to Kafka at {kafka_host}:{kafka_port}...")
                # Create a socket connection to check if Kafka is available
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)  # 2 second timeout
                result = sock.connect_ex((kafka_host, kafka_port))
                sock.close()
                
                if result == 0:
                    print(f"Successfully connected to Kafka at {kafka_host}:{kafka_port}")
                    connected = True
                else:
                    print(f"Kafka not yet available (attempt {attempt}/{max_attempts}), waiting...")
                    time.sleep(5)  # Wait before retrying
            except Exception as e:
                print(f"Error checking Kafka connection: {e}")
                time.sleep(5)  # Wait before retrying
        
        if not connected:
            print(f"Could not connect to Kafka after {max_attempts} attempts. Will keep trying with the Kafka client.")

    print(f"Connecting to Kafka broker: {os.environ.get('KAFKA_BROKER')}")
    print(f"Publishing to topic: {os.environ.get('TOPIC')}")
    
    config = {
        # User-specific properties that you must set
        'bootstrap.servers': os.environ.get("KAFKA_BROKER"),
        'client.id': socket.gethostname(),

        # Fixed properties
        'acks': 'all',
        # Add retry settings for robustness
        'retries': 5,
        'retry.backoff.ms': 500
    }

    MAX_RETRIES = 10
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            # Create Producer instance
            producer = Producer(config)
            
            # Test producer connection
            producer.list_topics(timeout=5)
            print("Successfully connected to Kafka!")
            break
            
        except Exception as e:
            retry_count += 1
            print(f"Failed to connect to Kafka (attempt {retry_count}/{MAX_RETRIES}): {e}")
            if retry_count >= MAX_RETRIES:
                print("Max retries reached. Exiting.")
                import sys
                sys.exit(1)
            time.sleep(5)  # Wait before retrying

    # Create an IoT device instance
    device_id = os.environ.get("DEVICE_ID", "device_1")
    refresh_rate = float(os.environ.get("REFRESH_RATE", 1))
    device = IoTDevice(device_id, refresh_rate)

    # Optional per-message delivery callback (triggered by poll() or flush())
    # when a message has been successfully delivered or permanently
    # failed delivery (after retries).
    def delivery_callback(err, msg):
        if err:
            print(f'ERROR: Message failed delivery: {err}')
        else:
            print(f"Produced event to topic {msg.topic()}: key = {msg.key().decode('utf-8')}, value length = {len(msg.value())}")

    # Produce data by selecting random values from these lists.
    topic = os.environ.get("TOPIC")
    sensor = device_id

    print(f"Starting producer loop for device {device_id} with refresh rate {refresh_rate} Hz")
    message_count = 0
    try:
        while True:
            message = device.emulate()
            producer.produce(topic=topic, value=message, key=sensor, callback=delivery_callback)
            producer.poll(0)
            
            message_count += 1
            if message_count % 100 == 0:
                print(f"Produced {message_count} messages so far")
                
            time.sleep(1/float(refresh_rate))  # Control message frequency
    except KeyboardInterrupt:
        print("Producer interrupted by user")
    except Exception as e:
        print(f"Error in producer: {e}")
    finally:
        # Flush any remaining messages
        producer.flush(30)
        print("Producer terminated")
