import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import streamlit_authenticator as stauth
from pathlib import Path
import yaml
from yaml.loader import SafeLoader
from io import BytesIO

# --------------------------------------------------------
# Authentication Configuration
# --------------------------------------------------------

# Define the path for the credentials YAML file
CREDENTIALS_PATH = Path(__file__).parent / "credentials.yaml"

# Check if credentials file exists
if not CREDENTIALS_PATH.exists():
    # If not, create a default credentials file
    default_credentials = {
        "credentials": {
            "usernames": {
                "user1": {
                    "name": "User One",
                    "password": "password1"
                },
                "user2": {
                    "name": "User Two",
                    "password": "password2"
                }
            }
        },
        "cookie": {
            "expiry_days": 30,
            "key": "some_signature_key",  # Replace with a secure key
            "name": "some_cookie_name"
        }
    }
    with open(CREDENTIALS_PATH, "w") as file:
        yaml.dump(default_credentials, file)

# Load credentials from YAML
with open(CREDENTIALS_PATH) as file:
    config = yaml.load(file, Loader=SafeLoader)

# Hash the passwords
hashed_passwords = stauth.Hasher([user["password"] for user in config["credentials"]["usernames"].values()]).generate()

# Assign hashed passwords back to the config
for (username, user), hashed_password in zip(config["credentials"]["usernames"].items(), hashed_passwords):
    config["credentials"]["usernames"][username]["password"] = hashed_password

# Initialize authenticator
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# Authenticate user
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
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
    
    # --------------------------------------------------------
    # Database Configuration
    # --------------------------------------------------------
    
    # Define the path for the SQLite database
    DB_PATH = Path(__file__).parent / "stakeholders.db"
    
    # Connect to the SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create the stakeholders table if it doesn't exist
    c.execute("""
        CREATE TABLE IF NOT EXISTS stakeholders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            power INTEGER NOT NULL,
            legitimacy INTEGER NOT NULL,
            urgency INTEGER NOT NULL
        )
    """)
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
                    if not (1 <= power <= 5 and 1 <= legitimacy <= 5 and 1 <= urgency <= 5):
                        raise ValueError("Power, Legitimacy, and Urgency must be between 1 and 5.")
    
                    # Insert the new stakeholder into the database
                    c.execute("""
                        INSERT INTO stakeholders (name, power, legitimacy, urgency)
                        VALUES (?, ?, ?, ?)
                    """, (name_input.strip(), power, legitimacy, urgency))
                    conn.commit()
    
                    st.sidebar.success(f"✅ Added stakeholder: **{name_input.strip()}**")
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
    
    # Retrieve stakeholders from the database
    c.execute("SELECT name, power, legitimacy, urgency FROM stakeholders")
    data = c.fetchall()
    
    # Convert to DataFrame
    stakeholders_df = pd.DataFrame(data, columns=['Name', 'Power', 'Legitimacy', 'Urgency'])
    
    if not stakeholders_df.empty:
        st.dataframe(stakeholders_df)
    
        # --------------------------------------------------------
        # Exporting Data
        # --------------------------------------------------------
    
        st.markdown("### 📥 Export Stakeholders Data")
        csv = stakeholders_df.to_csv(index=False).encode('utf-8')
        
        # Convert DataFrame to Excel in memory
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            stakeholders_df.to_excel(writer, index=False, sheet_name='Stakeholders')
        excel_data = buffer.getvalue()
        
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name='stakeholders.csv',
            mime='text/csv',
        )
        st.download_button(
            label="📑 Download Excel",
            data=excel_data,
            file_name='stakeholders.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
    
        # --------------------------------------------------------
        # Clear All Stakeholders
        # --------------------------------------------------------
    
        if st.button("🗑️ Clear All Stakeholders"):
            # Confirmation dialog
            if st.confirm("⚠️ Are you sure you want to delete all stakeholders?"):
                c.execute("DELETE FROM stakeholders")
                conn.commit()
                stakeholders_df = pd.DataFrame(columns=['Name', 'Power', 'Legitimacy', 'Urgency'])
                st.success("✅ All stakeholders have been cleared.")
            else:
                st.info("ℹ️ Action canceled.")
    
        # --------------------------------------------------------
        # Salience Categorization
        # --------------------------------------------------------
    
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
    
        stakeholders_df['Salience'] = stakeholders_df.apply(categorize_salience, axis=1)
    
        st.header("🗂️ Salience Categories")
        st.dataframe(stakeholders_df)
    
        # --------------------------------------------------------
        # Plotting the Salience Map
        # --------------------------------------------------------
    
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
    
    # --------------------------------------------------------
    # Logout Button
    # --------------------------------------------------------
    
    authenticator.logout("Logout", "sidebar")
    
    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------
    
    st.markdown("""
    ---
    *Created with ❤️ using Streamlit.*
    """)
    
    # Close the database connection when the app stops
    def close_connection():
        conn.close()
    
    st.on_session_end(close_connection)
    
elif authentication_status == False:
    st.error("⚠️ Username/password is incorrect")
elif authentication_status == None:
    st.warning("ℹ️ Please enter your username and password")