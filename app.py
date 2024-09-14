import streamlit as st
import pandas as pd
import plotly.express as px

# Set the page configuration
st.set_page_config(
    page_title="Stakeholder Salience Map",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title of the app
st.title("📊 Stakeholder Salience Map")

# Description
st.markdown("""
This application allows you to create and visualize a Stakeholder Salience Map based on **Power**, **Legitimacy**, and **Urgency** of stakeholders.
""")

# Initialize session state for stakeholders with specified data types
if 'stakeholders' not in st.session_state:
    st.session_state.stakeholders = pd.DataFrame({
        'Name': pd.Series(dtype='str'),
        'Power': pd.Series(dtype='int'),
        'Legitimacy': pd.Series(dtype='int'),
        'Urgency': pd.Series(dtype='int')
    })

# Sidebar for adding stakeholders
st.sidebar.header("Add a Stakeholder")

with st.sidebar.form("add_stakeholder_form"):
    name = st.text_input("Stakeholder Name")
    power = st.slider("Power", 1, 5, 3)
    legitimacy = st.slider("Legitimacy", 1, 5, 3)
    urgency = st.slider("Urgency", 1, 5, 3)
    submitted = st.form_submit_button("Add Stakeholder")

    if submitted:
        if name.strip():  # Ensures that the name is not just whitespace
            try:
                # Attempt to convert inputs to integers
                power = int(power)
                legitimacy = int(legitimacy)
                urgency = int(urgency)

                # Validate that the values are within the expected range
                if not (1 <= power <= 5 and 1 <= legitimacy <= 5 and 1 <= urgency <= 5):
                    raise ValueError("Power, Legitimacy, and Urgency must be between 1 and 5.")

                # Create a new stakeholder entry
                new_stakeholder = pd.DataFrame({
                    'Name': [name.strip()],
                    'Power': [power],
                    'Legitimacy': [legitimacy],
                    'Urgency': [urgency]
                })

                # Append the new stakeholder to the session state DataFrame
                st.session_state.stakeholders = pd.concat(
                    [st.session_state.stakeholders, new_stakeholder],
                    ignore_index=True
                )

                st.sidebar.success(f"✅ Added stakeholder: **{name.strip()}**")

            except ValueError as ve:
                st.sidebar.error(f"⚠️ Input Error: {ve}")
            except Exception as e:
                st.sidebar.error(f"⚠️ An unexpected error occurred: {e}")
        else:
            st.sidebar.error("⚠️ Please enter a valid stakeholder name.")

# Main area
st.header("📋 Stakeholders List")

if not st.session_state.stakeholders.empty:
    st.dataframe(st.session_state.stakeholders)

    # Button to clear all stakeholders
    if st.button("🗑️ Clear All Stakeholders"):
        st.session_state.stakeholders = pd.DataFrame({
            'Name': pd.Series(dtype='str'),
            'Power': pd.Series(dtype='int'),
            'Legitimacy': pd.Series(dtype='int'),
            'Urgency': pd.Series(dtype='int')
        })
        st.success("✅ All stakeholders have been cleared.")

    # Salience Categorization
    def categorize_salience(row):
        attributes = 0
        if row['Power'] >= 3:
            attributes += 1
        if row['Legitimacy'] >= 3:
            attributes += 1
        if row['Urgency'] >= 3:
            attributes += 1

        if attributes == 3:
            return 'Definitive'
        elif attributes == 2:
            if row['Power'] >= 3 and row['Legitimacy'] >= 3:
                return 'Dominant'
            elif row['Power'] >= 3 and row['Urgency'] >= 3:
                return 'Discretionary'
            elif row['Legitimacy'] >= 3 and row['Urgency'] >= 3:
                return 'Demanding'
        elif attributes == 1:
            if row['Power'] >= 3:
                return 'Dormant'
            elif row['Legitimacy'] >= 3:
                return 'Dependent'
            elif row['Urgency'] >= 3:
                return 'Dangerous'
        else:
            return 'Non-salient'

    stakeholders_df = st.session_state.stakeholders.copy()

    # Ensure numeric types
    stakeholders_df['Power'] = pd.to_numeric(stakeholders_df['Power'], errors='coerce')
    stakeholders_df['Legitimacy'] = pd.to_numeric(stakeholders_df['Legitimacy'], errors='coerce')
    stakeholders_df['Urgency'] = pd.to_numeric(stakeholders_df['Urgency'], errors='coerce')

    # Handle any NaN values that may have resulted from coercion
    stakeholders_df = stakeholders_df.dropna(subset=['Power', 'Legitimacy', 'Urgency'])

    stakeholders_df['Salience'] = stakeholders_df.apply(categorize_salience, axis=1)

    st.header("🗂️ Salience Categories")
    st.dataframe(stakeholders_df)

    # Plotting the Salience Map
    st.header("📈 Salience Map")

    # Define color mapping based on Salience
    color_map = {
        'Definitive': 'red',
        'Dominant': 'orange',
        'Discretionary': 'yellow',
        'Demanding': 'green',
        'Dormant': 'blue',
        'Dependent': 'purple',
        'Dangerous': 'brown',
        'Non-salient': 'gray'
    }

    stakeholders_df['Color'] = stakeholders_df['Salience'].map(color_map)

    # Create the scatter plot
    fig = px.scatter(
        stakeholders_df,
        x='Power',
        y='Legitimacy',
        size='Urgency',
        color='Salience',
        hover_name='Name',
        size_max=20,
        color_discrete_map=color_map,
        labels={
            'Power': 'Power',
            'Legitimacy': 'Legitimacy',
            'Urgency': 'Urgency'
        },
        title="🗺️ Stakeholder Salience Map"
    )

    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(tickmode='linear', dtick=1),
        legend_title="Salience Categories"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("ℹ️ No stakeholders added yet. Please add stakeholders from the sidebar.")

# Footer
st.markdown("""
---
*Created with ❤️ using Streamlit.*
""")
