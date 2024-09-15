import streamlit as st
import pandas as pd
import plotly.express as px
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
# State Management
# --------------------------------------------------------

if 'clear_stakeholders' not in st.session_state:
    st.session_state.clear_stakeholders = False

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
        return pd.read_sql_query("SELECT name, power, legitimacy, urgency FROM stakeholders", conn)

# Load stakeholders
stakeholders_df = load_stakeholders()

if not stakeholders_df.empty:
    st.dataframe(stakeholders_df)

    # --------------------------------------------------------
    # Exporting Data
    # --------------------------------------------------------

    st.markdown("### 📥 Export Stakeholders Data")
    csv = stakeholders_df.to_csv(index=False).encode("utf-8")

    # Convert DataFrame to Excel in memory
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        stakeholders_df.to_excel(writer, index=False, sheet_name="Stakeholders")
    excel_data = buffer.getvalue()

    st.download_button(
        label="📄 Download CSV",
        data=csv,
        file_name="stakeholders.csv",
        mime="text/csv",
    )
    st.download_button(
        label="📑 Download Excel",
        data=excel_data,
        file_name="stakeholders.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # --------------------------------------------------------
    # Clear All Stakeholders
    # --------------------------------------------------------

    if st.button("🗑️ Clear All Stakeholders"):
        st.session_state.clear_stakeholders = True

    if st.session_state.clear_stakeholders:
        # Confirmation dialog using radio buttons
        confirmation = st.radio(
            "⚠️ Are you sure you want to delete all stakeholders?",
            options=["No", "Yes"],
            index=0,
            horizontal=True,
        )
        if confirmation == "Yes":
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM stakeholders.db")
                conn.commit()
            st.success("✅ All stakeholders have been cleared.")
            st.cache_data.clear()  # Clear the cache to refresh the data
            st.session_state.clear_stakeholders = False
            st.rerun()
        else:
            st.info("ℹ️ Action canceled.")
            st.session_state.clear_stakeholders = False
            st.rerun()

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
    st.dataframe(stakeholders_df)

    # --------------------------------------------------------
    # Plotting the Salience Map
    # --------------------------------------------------------

    st.header("📈 Salience Map")

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
        size_max=20,
        color_discrete_map=color_map,
        labels={
            "power": "Power",
            "legitimacy": "Legitimacy",
            "urgency": "Urgency",
        },
        title="🗺️ Stakeholder Salience Map",
    )

    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(tickmode="linear", dtick=1),
        legend_title="Salience Categories",
    )

    st.plotly_chart(fig, use_container_width=True)

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
