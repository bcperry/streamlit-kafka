-- Basic queries for sensor data in PostgreSQL

-- Count records by device
SELECT device_id, COUNT(*) as record_count
FROM sensor_data
GROUP BY device_id
ORDER BY device_id;


-- Get latest 100 records
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
LIMIT 100;

-- Get min/max/avg values by device
SELECT 
    device_id,
    MIN(temperature) as min_temp,
    MAX(temperature) as max_temp,
    AVG(temperature) as avg_temp,
    MIN(humidity) as min_humidity,
    MAX(humidity) as max_humidity,
    AVG(humidity) as avg_humidity,
    MIN(pressure) as min_pressure,
    MAX(pressure) as max_pressure,
    AVG(pressure) as avg_pressure
FROM sensor_data
GROUP BY device_id;

-- Time-based analysis: hourly averages 
SELECT 
    device_id,
    date_trunc('hour', to_timestamp(timestamp)) as hour,
    AVG(temperature) as avg_temp,
    AVG(humidity) as avg_humidity,
    AVG(pressure) as avg_pressure,
    COUNT(*) as record_count
FROM sensor_data
GROUP BY device_id, date_trunc('hour', to_timestamp(timestamp))
ORDER BY device_id, hour;

-- Find potential anomalies (values outside 3 standard deviations)
WITH stats AS (
    SELECT 
        device_id,
        AVG(temperature) as avg_temp,
        STDDEV(temperature) as stddev_temp,
        AVG(humidity) as avg_humidity,
        STDDEV(humidity) as stddev_humidity,
        AVG(pressure) as avg_pressure,
        STDDEV(pressure) as stddev_pressure
    FROM sensor_data
    GROUP BY device_id
)
SELECT 
    s.id,
    s.device_id,
    s.temperature,
    s.humidity,
    s.pressure,
    to_timestamp(s.timestamp) as datetime
FROM sensor_data s
JOIN stats st ON s.device_id = st.device_id
WHERE 
    s.temperature > st.avg_temp + 3 * st.stddev_temp OR
    s.temperature < st.avg_temp - 3 * st.stddev_temp OR
    s.humidity > st.avg_humidity + 3 * st.stddev_humidity OR
    s.humidity < st.avg_humidity - 3 * st.stddev_humidity OR
    s.pressure > st.avg_pressure + 3 * st.stddev_pressure OR
    s.pressure < st.avg_pressure - 3 * st.stddev_pressure
ORDER BY s.timestamp DESC;
