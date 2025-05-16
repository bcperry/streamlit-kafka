# 📊 Streamlit Kafka IoT Analytics Dashboard

A real-time IoT sensor analytics dashboard that consumes data from Kafka topics and provides visualization and anomaly detection capabilities.

![Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B)
![Data Source](https://img.shields.io/badge/Data%20Source-Kafka-231F20)
![Analytics](https://img.shields.io/badge/Analytics-Real--time-blue)

## 🌟 Features

- **Real-time Data Consumption** - Stream IoT sensor data directly from Kafka topics
- **Interactive Visualizations** - Monitor temperature, humidity, and pressure readings in real-time
- **Anomaly Detection** - Identify unusual patterns in sensor data with multiple detection algorithms
- **PostgreSQL Data Persistence** - Store all sensor data in PostgreSQL for historical analysis
- **Multi-page Application** - Separate pages for data consumption, visualization, and anomaly detection
- **Azure ML Integration** - Ready for edge deployments and cloud connectivity

## 📋 Pages

1. **Home (Data Collection)** - Stream and view real-time data from Kafka topics
2. **📊 Visualizations** - Interactive charts and graphs for sensor data analysis
3. **🔍 Anomaly Detection** - Identify outliers using machine learning algorithms

## 🔧 Setup & Installation

### Prerequisites

- Python 3.8+
- Kafka broker running (local or remote)
- IoT devices producing data to Kafka topics

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd streamlit-kafka
```

2. **Set up environment variables**

Create a `.env` file in the root directory:

```
KAFKA_BROKER=localhost:9092
TOPIC=your-kafka-topic
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sensordata
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

3. **Install dependencies**

Using pip:
```bash
pip install -r requirements.txt
```

Using uv (recommended):
```bash
uv pip install -r requirements.txt
```

## 🚀 Usage

### Local Development

Run the application locally for development:

```bash
# Using standard Python:
streamlit run main.py

# Using uv (recommended):
uv run -- streamlit run main.py
```

### Producer Simulation

To simulate IoT devices sending data locally:

```bash
python producer.py
```

### Consuming Data Manually

For debugging or direct access to the Kafka consumer:

```bash
python consumer.py
```

### PostgreSQL Integration

To save data to PostgreSQL database:

```bash
# Start the Kafka to PostgreSQL connector
python kafka_to_postgres.py

# Query the PostgreSQL database
python query_postgres.py
```

### 🐳 Docker Deployment

Deploy the entire application stack with Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Run in the background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The Docker deployment includes:
- Zookeeper for Kafka coordination
- Kafka broker for message handling
- Kafka producer service for generating simulated IoT data
- Streamlit dashboard for data visualization and anomaly detection
- PostgreSQL database for persistent storage of sensor data
- Kafka-to-PostgreSQL connector for automated data transfer
- Kafka UI for topic monitoring and management

Access the dashboard at http://localhost:8501 after deployment.
Access the Kafka UI at http://localhost:8080 for monitoring Kafka topics.
Access PostgreSQL at localhost:5432 (username: postgres, password: postgres, database: sensordata).

## 🧠 Anomaly Detection Methods

This application offers multiple methods for detecting anomalies:

1. **Isolation Forest** - A machine learning algorithm that explicitly isolates anomalies
2. **Z-Score Method** - Detects outliers based on standard deviations from the mean
3. **IQR Method** - Uses interquartile ranges to identify statistical outliers

## 🛠️ Technology Stack

- **Streamlit** - Interactive web application framework
- **Apache Kafka** - Distributed event streaming platform
- **Pandas** - Data manipulation and analysis
- **Plotly** - Interactive visualizations
- **Scikit-Learn** - Machine learning for anomaly detection
- **Azure ML** - Cloud integration for edge deployments

## 📝 License

[MIT License](LICENSE)

## 👨‍💻 Contributions

Contributions welcome! Please feel free to submit a Pull Request.