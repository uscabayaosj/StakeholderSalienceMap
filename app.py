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

# Initialize session state for stakeholders
if 'stakeholders' not in st.session_state:
    st.session_state.stakeholders = pd.DataFrame(columns=['Name', 'Power', 'Legitimacy', 'Urgency'])

# Sidebar for adding stakeholders
st.sidebar.header("Add a Stakeholder")

with st.sidebar.form("add_stakeholder_form"):
    name = st.text_input("Stakeholder Name")
    power = st.slider("Power", 1, 5, 3)
    legitimacy = st.slider("Legitimacy", 1, 5, 3)
    urgency = st.slider("Urgency", 1, 5, 3)
    submitted = st.form_submit_button("Add Stakeholder")

    if submitted:
        if name:
            new_stakeholder = pd.DataFrame({
                'Name': [name],
                'Power': [power],
                'Legitimacy': [legitimacy],
                'Urgency': [urgency]
            })
            st.session_state.stakeholders = pd.concat([st.session_state.stakeholders, new_stakeholder], ignore_index=True)
            st.sidebar.success(f"Added stakeholder: {name}")
        else:
            st.sidebar.error("Please enter a stakeholder name.")

# Main area
st.header("Stakeholders List")

if not st.session_state.stakeholders.empty:
    st.dataframe(st.session_state.stakeholders)

    # Button to clear all stakeholders
    if st.button("Clear All Stakeholders"):
        st.session_state.stakeholders = pd.DataFrame(columns=['Name', 'Power', 'Legitimacy', 'Urgency'])
        st.success("All stakeholders have been cleared.")

    # Salience Categorization
    def categorize_salience(row):
        attributes = 0
        if row['Power'] >=3:
            attributes +=1
        if row['Legitimacy'] >=3:
            attributes +=1
        if row['Urgency'] >=3:
            attributes +=1

        if attributes == 3:
            return 'Definitive'
        elif attributes ==2:
            if row['Power'] >=3 and row['Legitimacy'] >=3:
                return 'Dominant'
            elif row['Power'] >=3 and row['Urgency'] >=3:
                return 'Discretionary'
            elif row['Legitimacy'] >=3 and row['Urgency'] >=3:
                return 'Demanding'
        elif attributes ==1:
            if row['Power'] >=3:
                return 'Dormant'
            elif row['Legitimacy'] >=3:
                return 'Dependent'
            elif row['Urgency'] >=3:
                return 'Dangerous'
        else:
            return 'Non-salient'

    stakeholders_df = st.session_state.stakeholders.copy()
    stakeholders_df['Salience'] = stakeholders_df.apply(categorize_salience, axis=1)

    st.header("Salience Categories")
    st.dataframe(stakeholders_df)

    # Plotting the Salience Map
    st.header("Salience Map")

    # Define color mapping based on Salience
    salience_categories = stakeholders_df['Salience'].unique()
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
        title="Stakeholder Salience Map"
    )

    fig.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis=dict(tickmode='linear', dtick=1),
        legend_title="Salience Categories"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No stakeholders added yet. Please add stakeholders from the sidebar.")

# Footer
st.markdown("""
---
*Created with ❤️ using Streamlit.*
""")