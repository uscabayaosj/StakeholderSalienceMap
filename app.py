import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from pathlib import Path
from io import BytesIO

# --------------------------------------------------------
# Page Configuration
# --------------------------------------------------------

st.set_page_config(
    page_title="Stakeholder Salience Map",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title of the app
st.title("📊 Stakeholder Salience Map")

# Description
st.markdown(
    """
This application allows you to create and visualize a Stakeholder Salience Map based on **Power**, **Legitimacy**, and **Urgency** of stakeholders.
"""
)

# --------------------------------------------------------
# Database Configuration
# --------------------------------------------------------

# Define the path for the SQLite database
DB_PATH = Path(__file__).parent / "stakeholders.db"

# Function to get database connection
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Create the stakeholders table if it doesn't exist
with get_connection() as conn:
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS stakeholders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            power INTEGER NOT NULL,
            legitimacy INTEGER NOT NULL,
            urgency INTEGER NOT NULL
        )
    """
    )
    conn.commit()

# --------------------------------------------------------
# Sidebar for Adding Stakeholders
# --------------------------------------------------------

st.sidebar.header("Add a Stakeholder")

with st.sidebar.form("add_stakeholder_form"):
    name_input = st.text_input("Stakeholder Name")
    power = st.slider("Power", 1, 5, 3)
    legitimacy = st.slider("Legitimacy", 1, 5, 3)
    urgency = st.slider("Urgency", 1, 5, 3)
    submitted = st.form_submit_button("Add Stakeholder")

    if submitted:
        if name_input.strip():  # Ensure the name is not empty or just whitespace
            try:
                # Validate the numeric inputs are within the expected range
                if not (
                    1 <= power <= 5 and 1 <= legitimacy <= 5 and 1 <= urgency <= 5
                ):
                    raise ValueError(
                        "Power, Legitimacy, and Urgency must be between 1 and 5."
                    )

                # Insert the new stakeholder into the database
                with get_connection() as conn:
                    c = conn.cursor()
                    c.execute(
                        """
                        INSERT INTO stakeholders (name, power, legitimacy, urgency)
                        VALUES (?, ?, ?, ?)
                    """,
                        (name_input.strip(), power, legitimacy, urgency),
                    )
                    conn.commit()

                st.sidebar.success(f"✅ Added stakeholder: **{name_input.strip()}**")
                st.rerun()  # Rerun the app to refresh the data
            except ValueError as ve:
                st.sidebar.error(f"⚠️ Input Error: {ve}")
            except Exception as e:
                st.sidebar.error(f"⚠️ An unexpected error occurred: {e}")
        else:
            st.sidebar.error("⚠️ Please enter a valid stakeholder name.")

# --------------------------------------------------------
# Main Area: Display Stakeholders and Salience Map
# --------------------------------------------------------

st.header("📋 Stakeholders List")

# Function to load stakeholders from the database
@st.cache_data(ttl=1)
def load_stakeholders():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT id, name, power, legitimacy, urgency FROM stakeholders", conn)

# Function to delete a stakeholder
def delete_stakeholder(stakeholder_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM stakeholders WHERE id = ?", (stakeholder_id,))
        conn.commit()
    st.cache_data.clear()
    st.rerun()

# Load stakeholders
stakeholders_df = load_stakeholders()

if not stakeholders_df.empty:
    # Create a stylish display for stakeholders
    st.markdown("""
    <style>
    .stakeholder-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stakeholder-name {
        font-weight: bold;
        font-size: 18px;
    }
    .stakeholder-attribute {
        display: inline-block;
        margin-right: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    for index, row in stakeholders_df.iterrows():
        st.markdown(f"""
        <div class="stakeholder-box">
            <p class="stakeholder-name">{row['name']}</p>
            <p>
                <span class="stakeholder-attribute">Power: {row['power']}</span>
                <span class="stakeholder-attribute">Legitimacy: {row['legitimacy']}</span>
                <span class="stakeholder-attribute">Urgency: {row['urgency']}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Delete {row['name']}", key=f"delete_{row['id']}"):
            delete_stakeholder(row['id'])

    # --------------------------------------------------------
    # Exporting Data
    # --------------------------------------------------------

    st.markdown("### 📥 Export Stakeholders Data")
    col1, col2 = st.columns(2)
    
    csv = stakeholders_df.to_csv(index=False).encode("utf-8")
    col1.download_button(
        label="📄 Download CSV",
        data=csv,
        file_name="stakeholders.csv",
        mime="text/csv",
    )

    # Convert DataFrame to Excel in memory
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        stakeholders_df.to_excel(writer, index=False, sheet_name="Stakeholders")
    excel_data = buffer.getvalue()
    
    col2.download_button(
        label="📑 Download Excel",
        data=excel_data,
        file_name="stakeholders.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # --------------------------------------------------------
    # Salience Categorization
    # --------------------------------------------------------

    def categorize_salience(row):
        attributes = 0
        if row["power"] >= 3:
            attributes += 1
        if row["legitimacy"] >= 3:
            attributes += 1
        if row["urgency"] >= 3:
            attributes += 1

        if attributes == 3:
            return "Definitive"
        elif attributes == 2:
            if row["power"] >= 3 and row["legitimacy"] >= 3:
                return "Dominant"
            elif row["power"] >= 3 and row["urgency"] >= 3:
                return "Dangerous"
            elif row["legitimacy"] >= 3 and row["urgency"] >= 3:
                return "Dependent"
        elif attributes == 1:
            if row["power"] >= 3:
                return "Dormant"
            elif row["legitimacy"] >= 3:
                return "Discretionary"
            elif row["urgency"] >= 3:
                return "Demanding"
        else:
            return "Non-salient"

    stakeholders_df["Salience"] = stakeholders_df.apply(categorize_salience, axis=1)

    st.header("🗂️ Salience Categories")
    st.dataframe(stakeholders_df[["name", "power", "legitimacy", "urgency", "Salience"]])

    # --------------------------------------------------------
    # Plotting the Salience Map
    # --------------------------------------------------------

    st.header("📈 Salience Map")

    # Add detailed legend explanation
    st.markdown("""
    ### Legend Explanation

    This bubble plot visualizes stakeholders based on their Power, Legitimacy, and Urgency:

    - **X-axis**: Represents the **Power** of the stakeholder (scale 1-5)
    - **Y-axis**: Represents the **Legitimacy** of the stakeholder (scale 1-5)
    - **Bubble Size**: Represents the **Urgency** of the stakeholder (larger bubbles indicate higher urgency)
    - **Color**: Represents the **Salience Category** of the stakeholder

    #### Salience Categories:

    1. **Definitive** (Red): High in all attributes (Power, Legitimacy, Urgency)
    2. **Dominant** (Orange): High in Power and Legitimacy
    3. **Dangerous** (Brown): High in Power and Urgency
    4. **Dependent** (Purple): High in Legitimacy and Urgency
    5. **Dormant** (Blue): High in Power only
    6. **Discretionary** (Green): High in Legitimacy only
    7. **Demanding** (Yellow): High in Urgency only
    8. **Non-salient** (Gray): Low in all attributes

    *Note: "High" is considered a score of 3 or above on the 1-5 scale.*

    Hover over each bubble to see the stakeholder's name and exact scores.
    """)

    # Define color mapping based on Salience
    color_map = {
        "Definitive": "red",
        "Dominant": "orange",
        "Dangerous": "brown",
        "Dependent": "purple",
        "Dormant": "blue",
        "Discretionary": "green",
        "Demanding": "yellow",
        "Non-salient": "gray",
    }

    stakeholders_df["Color"] = stakeholders_df["Salience"].map(color_map)

    # Create the scatter plot
    fig = px.scatter(
        stakeholders_df,
        x="power",
        y="legitimacy",
        size="urgency",
        color="Salience",
        hover_name="name",
        hover_data=["power", "legitimacy", "urgency"],
        size_max=30,
        color_discrete_map=color_map,
        labels={
            "power": "Power",
            "legitimacy": "Legitimacy",
            "urgency": "Urgency",
        },
        title="🗺️ Stakeholder Salience Map",
    )

    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1, range=[0.5, 5.5]),
        yaxis=dict(tickmode="linear", dtick=1, range=[0.5, 5.5]),
        legend_title="Salience Categories",
    )

    st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------------
    # Spider Chart Visualization
    # --------------------------------------------------------

    st.header("🕸️ Spider Chart Visualization")

    # Allow user to select stakeholders for the spider chart
    selected_stakeholders = st.multiselect(
        "Select stakeholders to include in the spider chart:",
        options=stakeholders_df['name'].tolist(),
        default=stakeholders_df['name'].tolist()[:5]  # Default to first 5 stakeholders
    )

    if selected_stakeholders:
        # Filter the dataframe based on selected stakeholders
        selected_df = stakeholders_df[stakeholders_df['name'].isin(selected_stakeholders)]

        # Create the spider chart
        fig = go.Figure()

        for _, row in selected_df.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row['power'], row['legitimacy'], row['urgency'], row['power']],
                theta=['Power', 'Legitimacy', 'Urgency', 'Power'],
                fill='toself',
                name=row['name']
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5]
                )),
            showlegend=True,
            title="Stakeholder Comparison Spider Chart"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please select at least one stakeholder to display the spider chart.")

else:
    st.info("ℹ️ No stakeholders added yet. Please add stakeholders from the sidebar.")

# --------------------------------------------------------
# Footer
# --------------------------------------------------------

st.markdown(
    """
---
*Created with ❤️ using Streamlit.*
"""
)
