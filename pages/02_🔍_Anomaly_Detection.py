import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import plotly.figure_factory as ff

# Configure the Streamlit page
st.set_page_config(page_title="Anomaly Detection", page_icon="🔍", layout="wide")

st.title('🔍 Anomaly Detection')
st.write("Find anomalies in your sensor data using machine learning")

# Check if we have data
if 'data_df' not in st.session_state or st.session_state.data_df.empty:
    st.info("No data available yet. Please go to the Home page to start collecting data first.")
else:
    data_df = st.session_state.data_df.copy()
    
    # Display the dataframe
    st.subheader("Sensor Data")
    st.dataframe(data_df)
    
    st.divider()
    
    # Anomaly Detection Settings
    st.subheader("Anomaly Detection Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        contamination = st.slider("Contamination Factor", min_value=0.01, max_value=0.5, value=0.1, step=0.01,
                                help="Expected proportion of outliers in the data. Lower values are more selective.")
    
    with col2:
        features = st.multiselect(
            "Features to analyze",
            options=["temperature", "humidity", "pressure"],
            default=["temperature", "humidity", "pressure"],
            help="Select the sensor measurements to include in anomaly detection"
        )
    
    with col3:
        # Let user input threshold for Z-score method
        threshold = st.slider("Z-Score Threshold", min_value=1.0, max_value=5.0, value=3.0, step=0.1,
                            help="Number of standard deviations to consider as anomalous")
    
    method = st.radio("Detection Method", options=["Isolation Forest", "Z-Score", "IQR Method"],
                    help="Algorithm to use for anomaly detection")

    # Make sure features are selected
    if not features:
        st.warning("Please select at least one feature for anomaly detection.")
    else:
        # Get the data for the selected features
        if st.button("Detect Anomalies"):
            # Make sure we have enough data
            if len(data_df) < 10:
                st.error("Not enough data points for anomaly detection. Need at least 10 data points.")
            else:
                with st.spinner("Detecting anomalies..."):
                    # Preparing the data
                    X = data_df[features].copy()
                    
                    # Handle NaN values
                    X = X.fillna(X.mean())
                    
                    if method == "Isolation Forest":
                        # Apply Isolation Forest
                        model = IsolationForest(contamination=contamination, random_state=42)
                        data_df["anomaly"] = model.fit_predict(X)
                        # Convert to boolean (1 is inlier, -1 is outlier in Isolation Forest)
                        data_df["is_anomaly"] = data_df["anomaly"] == -1
                        
                        # Feature importance 
                        st.subheader("Feature Contributions to Anomaly Detection")
                        feature_scores = {}
                        for feature in features:
                            temp_X = X.copy()
                            # Shuffle one feature to see impact on anomaly scores
                            temp_X[feature] = np.random.permutation(temp_X[feature].values)
                            temp_scores = model.decision_function(temp_X)
                            original_scores = model.decision_function(X)
                            # Calculate feature importance as difference in scores
                            feature_scores[feature] = np.mean(np.abs(original_scores - temp_scores))
                        
                        # Normalize feature importance scores
                        total_importance = sum(feature_scores.values())
                        if total_importance > 0:  # Avoid division by zero
                            for feature in feature_scores:
                                feature_scores[feature] /= total_importance
                                
                        # Display feature importance
                        fig_importance = px.bar(
                            x=list(feature_scores.keys()),
                            y=list(feature_scores.values()),
                            labels={"x": "Feature", "y": "Importance"},
                            title="Feature Importance in Anomaly Detection"
                        )
                        st.plotly_chart(fig_importance, use_container_width=True)
                        
                    elif method == "Z-Score":
                        # Apply Z-Score method
                        scaler = StandardScaler()
                        scaled_features = scaler.fit_transform(X)
                        
                        # Compute the Euclidean distance from origin (0,0,...) in the standardized space
                        # This gives a single score for multivariate data
                        data_df["zscore"] = np.sqrt(np.sum(scaled_features ** 2, axis=1))
                        data_df["is_anomaly"] = data_df["zscore"] > threshold
                        
                    else:  # IQR Method
                        # Apply IQR method
                        data_df["is_anomaly"] = False
                        
                        # Calculate lower and upper bounds for each feature
                        for feature in features:
                            Q1 = data_df[feature].quantile(0.25)
                            Q3 = data_df[feature].quantile(0.75)
                            IQR = Q3 - Q1
                            lower_bound = Q1 - 1.5 * IQR
                            upper_bound = Q3 + 1.5 * IQR
                            
                            # Mark as anomaly if outside bounds
                            feature_anomalies = (data_df[feature] < lower_bound) | (data_df[feature] > upper_bound)
                            data_df["is_anomaly"] = data_df["is_anomaly"] | feature_anomalies
                    
                    # Count anomalies
                    anomaly_count = data_df["is_anomaly"].sum()
                    
                    # Display results
                    st.subheader(f"Detected {anomaly_count} anomalies out of {len(data_df)} data points")
                    
                    # Filter and show anomalies
                    anomalies_df = data_df[data_df["is_anomaly"]].copy()
                    
                    st.subheader("Anomalous Data Points")
                    if anomalies_df.empty:
                        st.info("No anomalies detected with the current settings.")
                    else:
                        st.dataframe(anomalies_df)
                    
                    # Visualization of all data points with anomalies highlighted
                    st.subheader("Visualizing Anomalies")
                    
                    tab1, tab2, tab3 = st.tabs(["Time Series", "Feature Relationships", "Distribution"])
                    
                    with tab1:
                        # Time Series visualization
                        for feature in features:
                            fig = go.Figure()
                            
                            # Add normal points
                            fig.add_trace(go.Scatter(
                                x=data_df[~data_df["is_anomaly"]]["timestamp"],
                                y=data_df[~data_df["is_anomaly"]][feature],
                                mode="markers",
                                name="Normal",
                                marker=dict(color="blue", size=8)
                            ))
                            
                            # Add anomalous points
                            fig.add_trace(go.Scatter(
                                x=data_df[data_df["is_anomaly"]]["timestamp"],
                                y=data_df[data_df["is_anomaly"]][feature],
                                mode="markers",
                                name="Anomaly",
                                marker=dict(color="red", size=12, symbol="circle-open")
                            ))
                            
                            fig.update_layout(
                                title=f"{feature} Over Time with Anomalies",
                                xaxis_title="Timestamp",
                                yaxis_title=feature.capitalize(),
                                legend_title="Data Point Type",
                                hovermode="closest"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        # Scatter plot matrix for feature relationships
                        if len(features) >= 2:
                            # Create scatter plots for each pair of features
                            for i, feature1 in enumerate(features):
                                for feature2 in features[i+1:]:
                                    fig = go.Figure()
                                    
                                    # Add normal points
                                    fig.add_trace(go.Scatter(
                                        x=data_df[~data_df["is_anomaly"]][feature1],
                                        y=data_df[~data_df["is_anomaly"]][feature2],
                                        mode="markers",
                                        name="Normal",
                                        marker=dict(color="blue", size=8)
                                    ))
                                    
                                    # Add anomalous points
                                    fig.add_trace(go.Scatter(
                                        x=data_df[data_df["is_anomaly"]][feature1],
                                        y=data_df[data_df["is_anomaly"]][feature2],
                                        mode="markers",
                                        name="Anomaly",
                                        marker=dict(color="red", size=12, symbol="circle-open")
                                    ))
                                    
                                    fig.update_layout(
                                        title=f"{feature1} vs {feature2} with Anomalies",
                                        xaxis_title=feature1.capitalize(),
                                        yaxis_title=feature2.capitalize(),
                                        legend_title="Data Point Type",
                                        hovermode="closest"
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Select at least two features to see relationships between them.")
                    
                    with tab3:
                        # Distribution visualization
                        for feature in features:
                            # Create histogram with both normal and anomalous points
                            fig = go.Figure()
                            
                            fig.add_trace(go.Histogram(
                                x=data_df[~data_df["is_anomaly"]][feature],
                                name="Normal",
                                marker_color="blue",
                                opacity=0.7
                            ))
                            
                            fig.add_trace(go.Histogram(
                                x=data_df[data_df["is_anomaly"]][feature],
                                name="Anomaly",
                                marker_color="red",
                                opacity=0.7
                            ))
                            
                            fig.update_layout(
                                title=f"Distribution of {feature} Values",
                                xaxis_title=feature.capitalize(),
                                yaxis_title="Count",
                                barmode="overlay",
                                legend_title="Data Point Type"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Add box plot for clearer visualization of the distribution
                            box_fig = go.Figure()
                            
                            box_fig.add_trace(go.Box(
                                y=data_df[~data_df["is_anomaly"]][feature],
                                name="Normal",
                                marker_color="blue"
                            ))
                            
                            box_fig.add_trace(go.Box(
                                y=data_df[data_df["is_anomaly"]][feature],
                                name="Anomaly",
                                marker_color="red"
                            ))
                            
                            box_fig.update_layout(
                                title=f"Box Plot of {feature} Values",
                                yaxis_title=feature.capitalize(),
                                showlegend=True
                            )
                            
                            st.plotly_chart(box_fig, use_container_width=True)
                    
                    # Provide insights and recommendations
                    if anomaly_count > 0:
                        st.subheader("Insights and Recommendations")
                        
                        # Calculate some statistics for the anomalies
                        anomaly_insights = []
                        
                        for feature in features:
                            if not anomalies_df.empty:
                                # Get the min, max, and average for anomalies
                                anomaly_min = anomalies_df[feature].min()
                                anomaly_max = anomalies_df[feature].max()
                                anomaly_avg = anomalies_df[feature].mean()
                                
                                # Get the min, max, and average for normal data
                                normal_min = data_df[~data_df["is_anomaly"]][feature].min()
                                normal_max = data_df[~data_df["is_anomaly"]][feature].max()
                                normal_avg = data_df[~data_df["is_anomaly"]][feature].mean()
                                
                                # If anomalies are higher or lower than normal range
                                if anomaly_max > normal_max:
                                    anomaly_insights.append(f"- {feature.capitalize()} shows unusually high values (max: {anomaly_max:.2f} vs normal max: {normal_max:.2f})")
                                if anomaly_min < normal_min:
                                    anomaly_insights.append(f"- {feature.capitalize()} shows unusually low values (min: {anomaly_min:.2f} vs normal min: {normal_min:.2f})")
                                
                                # If anomaly average is significantly different
                                if abs(anomaly_avg - normal_avg) > 0.1 * abs(normal_avg):
                                    anomaly_insights.append(f"- {feature.capitalize()} anomalies have a significantly different average ({anomaly_avg:.2f}) compared to normal data ({normal_avg:.2f})")
                        
                        # Check when anomalies occurred
                        if not anomalies_df.empty and 'timestamp' in anomalies_df.columns:
                            # Convert timestamp to datetime if it's not already
                            if not pd.api.types.is_datetime64_any_dtype(anomalies_df['timestamp']):
                                try:
                                    # Try to convert if it's a number (unix timestamp)
                                    anomalies_df['timestamp_dt'] = pd.to_datetime(anomalies_df['timestamp'], unit='s')
                                except:
                                    # If that fails, try the default conversion
                                    try:
                                        anomalies_df['timestamp_dt'] = pd.to_datetime(anomalies_df['timestamp'])
                                    except:
                                        # If all conversions fail, skip time-based insights
                                        pass
                            else:
                                anomalies_df['timestamp_dt'] = anomalies_df['timestamp']
                                
                            if 'timestamp_dt' in anomalies_df.columns:
                                # Check if anomalies cluster in time
                                if len(anomalies_df) >= 2:
                                    anomalies_df = anomalies_df.sort_values('timestamp_dt')
                                    time_diffs = np.diff(anomalies_df['timestamp_dt'].astype(np.int64) / 10**9)  # Convert to seconds
                                    
                                    # If the average time between anomalies is less than half the average time between all points,
                                    # the anomalies might be clustered
                                    if 'timestamp_dt' in anomalies_df.columns:
                                        all_time_diffs = np.diff(data_df['timestamp'].astype(float))
                                        if len(all_time_diffs) > 0 and len(time_diffs) > 0:
                                            avg_time_diff = np.mean(all_time_diffs)
                                            avg_anomaly_time_diff = np.mean(time_diffs)
                                            
                                            if avg_anomaly_time_diff < avg_time_diff / 2:
                                                anomaly_insights.append(f"- Anomalies appear to be clustered in time, suggesting a potential systematic issue during those periods")
                        
                        # Device-specific anomalies
                        if 'device_id' in data_df.columns and not anomalies_df.empty:
                            device_counts = anomalies_df['device_id'].value_counts()
                            total_device_counts = data_df['device_id'].value_counts()
                            
                            for device, count in device_counts.items():
                                device_anomaly_rate = count / total_device_counts.get(device, 0)
                                if device_anomaly_rate > contamination * 2:  # Using 2x the expected contamination as a threshold
                                    anomaly_insights.append(f"- Device {device} has a higher than expected anomaly rate ({device_anomaly_rate:.1%})")
                        
                        # Display insights
                        if anomaly_insights:
                            for insight in anomaly_insights:
                                st.markdown(insight)
                            
                            # Recommendations based on insights
                            st.subheader("Recommendations")
                            st.markdown("""
                            Based on the anomalies detected, consider the following actions:
                            
                            1. **Investigate Device Performance**: Check the physical condition and calibration of sensors showing frequent anomalies.
                            
                            2. **Review Environmental Conditions**: External factors might be affecting sensor readings during specific time periods.
                            
                            3. **Validate Sensor Data**: Cross-reference anomalous readings with other sensors or measurement systems.
                            
                            4. **Adjust Detection Parameters**: If too many/few anomalies are detected, adjust the sensitivity parameters.
                            
                            5. **Set Up Alerts**: Consider implementing real-time anomaly detection alerts for critical deviations.
                            """)
                        else:
                            st.info("No specific insights could be generated for the detected anomalies.")
