import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Kafka Data Visualizations", page_icon="📊", layout="wide")

st.title('📊 Data Visualizations')
st.write("Visualizations of the data collected from Kafka topics")

# Check if we have data
if 'data_df' not in st.session_state or st.session_state.data_df.empty:
    st.info("No data available yet. Please go to the Home page to start collecting data first.")
else:
    data_df = st.session_state.data_df
    
    # Display the dataframe
    st.subheader(f"Latest Events (showing {len(data_df)} of max 500)")
    st.dataframe(data_df)
    
    # Create visualizations
    try:
        # Create a plotly express line chart for time series data
        fig = px.line(
            data_df,
            x='timestamp', 
            y=['temperature', 'humidity', 'pressure'],
            title='Sensor Measurements Over Time',
            labels={
                'timestamp': 'Time',
                'value': 'Measurement',
                'variable': 'Metric'
            }
        )
        # Improve layout
        fig.update_layout(
            legend_title_text='Sensor Data',
            xaxis_title='Time',
            yaxis_title='Value',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a secondary chart showing distribution
        col1, col2 = st.columns(2)
        with col1:
            hist_fig = px.histogram(
                data_df, 
                x="temperature",
                title="Temperature Distribution"
            )
            st.plotly_chart(hist_fig, use_container_width=True)
        
        with col2:
            scatter_fig = px.scatter(
                data_df,
                x="humidity", 
                y="temperature",
                color="device_id",
                title="Temperature vs Humidity"
            )
            st.plotly_chart(scatter_fig, use_container_width=True)
            
    except Exception as viz_error:
        st.warning(f"Couldn't create visualization: {viz_error}")
