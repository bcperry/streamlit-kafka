import streamlit as st
import numpy as np
import os
from sklearn.cluster import MiniBatchKMeans
from confluent_kafka import Consumer, KafkaError as Error
from dotenv import load_dotenv
import pandas as pd
import json

# Configure the Streamlit page
st.set_page_config(page_title="Azure ML at the Edge", page_icon="🏠", layout="wide")

load_dotenv(".env")

@st.cache_resource
def create_kafka_consumer():
    """
    Create a Kafka consumer instance.
    This function is called once and the result is cached for performance.
    """
    config = {
            # User-specific properties that you must set
            'bootstrap.servers': os.environ.get("KAFKA_BROKER"),

            # Fixed properties
            'group.id':          'kafka-python-getting-started',
            'auto.offset.reset': 'earliest'
        }

    # Create Consumer instance
    consumer = Consumer(config)

    topics = consumer.list_topics()
    topic_list = [topic for topic in topics.topics]
    filtered_topics = [topic for topic in topic_list if not topic.startswith("__")]

    consumer.subscribe([f'{os.environ.get("TOPIC")}'])

    return consumer, filtered_topics

# For simplicity, let's simulate reading from a file or shared memory
# where we keep the cluster data updated. In a real system, you might connect
# to a Redis store or a DB that the consumer updates.

def get_latest_data():
    """
    Placeholder for reading points + cluster centers from a shared resource.
    Could be a memory-based approach, a database, or a separate Kafka topic 
    storing cluster assignments.
    Here, we'll just randomly generate data to emulate real-time updates.
    """
    # random data
    X = np.random.rand(50, 2) * 10
    # A fake K-Means model to label them for demonstration
    kmeans = MiniBatchKMeans(n_clusters=3).fit(X)
    return X, kmeans.labels_, kmeans.cluster_centers_



# Initialize session state variables
if "data_df" not in st.session_state:
    st.session_state.data_df = pd.DataFrame(columns=['device_id', 'temperature', 'humidity', 'pressure', 'timestamp'])

if st.session_state.get("polling") is None:
    st.toast("Initializing session state variables")
    # Initialize session state variables
    st.session_state.polling = True
    st.session_state.selected_topics = []

# Streamlit UI
st.title('🏠 Azure ML at the Edge')
st.write("Kafka topic consumer for IoT device data")

# Create tabs for different actions
tab1, tab2 = st.tabs(["Data Collection", "Settings"])

with tab1:
    st.write(f"Consuming topic from {os.environ.get('TOPIC')}")

    # Add a button to control consumer status
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Consuming", key="start_consuming", use_container_width=True):
            st.session_state.polling = True
            st.success("Started consuming messages!")
    
    with col2:
        if st.button("Stop Consuming", key="stop_consuming", use_container_width=True):
            st.session_state.polling = False
            st.warning("Stopped consuming messages!")

    st.divider()
    
    # Create a placeholder for the data display
    placeholder = st.empty()

# Only consume messages if polling is enabled
if st.session_state.polling:
    # Create a Kafka consumer
    with st.spinner("Creating Kafka consumer..."):
        consumer, topics = create_kafka_consumer()
    
    try:
        # We use Streamlit's 'while True' approach in a "streamlit run" context 
        while st.session_state.polling:
            msg = consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                pass
            elif msg.error():
                st.error(f"ERROR: {msg.error()}")
            else:
                # Extract the (optional) key and value
                try:
                    value_str = msg.value().decode('utf-8')
                    data = json.loads(value_str)
                    
                    # Append new data to the DataFrame
                    new_row = pd.DataFrame([data])
                    st.session_state.data_df = pd.concat([st.session_state.data_df, new_row], ignore_index=True)
                    
                    # Keep only the last 500 events
                    if len(st.session_state.data_df) > 500:
                        st.session_state.data_df = st.session_state.data_df.iloc[-500:]
                    
                    # Display the dataframe
                    with placeholder.container():
                        st.subheader(f"Latest Events (showing {len(st.session_state.data_df)} of max 500)")
                        st.dataframe(st.session_state.data_df)
                        
                        # Add navigation hints
                        st.info("📊 Go to the 'Visualizations' page to view charts and analyze the data")
                        st.info("🔍 Go to the 'Anomaly Detection' page to identify unusual patterns in your data")
                        
                except json.JSONDecodeError:
                    st.error(f"Failed to parse message as JSON: {value_str}")
                except KeyError as e:
                    st.error(f"Missing expected field in message: {e}")
    
    except Error as e:
        st.warning(f"Error: {e}")
    
    # finally:
    #     # Leave group and commit final offsets
    #     consumer.close()
else:
    # Display the data we've collected so far when not polling
    with placeholder.container():
        if st.session_state.data_df.empty:
            st.info("No data collected yet. Click 'Start Consuming' to begin.")
        else:
            st.subheader(f"Latest Events (showing {len(st.session_state.data_df)} of max 500)")
            st.dataframe(st.session_state.data_df)
            st.info("Currently not consuming messages. Click 'Start Consuming' to resume.")
            st.info("📊 Go to the 'Visualizations' page to view charts and analyze the data")
            st.info("🔍 Go to the 'Anomaly Detection' page to identify unusual patterns in your data")

with tab2:
    st.subheader("Kafka Connection Settings")
    st.text_input("Kafka Broker", value=os.environ.get("KAFKA_BROKER"), disabled=True)
    st.text_input("Topic", value=os.environ.get("TOPIC", ""), disabled=True)
    st.write("Settings are managed through environment variables in the `.env` file")
