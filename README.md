# Stakeholder Salience Map App

## 📊 Overview

The Stakeholder Salience Map App is a Streamlit-based web application designed to help users create, visualize, and analyze stakeholder salience based on the attributes of Power, Legitimacy, and Urgency. This tool is particularly useful for project managers, business analysts, and decision-makers who need to understand and prioritize stakeholders in their projects or initiatives.

## ✨ Features

- **Add Stakeholders**: Easily input stakeholder information, including name and scores for Power, Legitimacy, and Urgency.
- **Stakeholder List**: View all added stakeholders in a clean, styled list format.
- **Individual Deletion**: Remove specific stakeholders from the list as needed.
- **Data Export**: Download stakeholder data in CSV or Excel format for further analysis.
- **Salience Categorization**: Automatically categorize stakeholders based on their attribute scores.
- **Interactive Salience Map**: Visualize stakeholders in a bubble plot, with size and color indicating different attributes and categories.
- **Spider Chart Comparison**: Select and compare multiple stakeholders using an interactive spider chart.
- **Detailed Explanations**: Understand the Salience Map and categories with comprehensive in-app explanations.

## 🛠️ Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/stakeholder-salience-map.git
   cd stakeholder-salience-map
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## 🚀 Usage

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. Open your web browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).

3. Use the sidebar to add new stakeholders by entering their name and scoring their Power, Legitimacy, and Urgency on a scale of 1-5.

4. View the list of stakeholders, export data, and analyze the Salience Map and Spider Chart visualizations in the main area of the app.

## 📖 How It Works

The app uses the following criteria to categorize stakeholders:

- **Definitive**: High in all attributes (Power, Legitimacy, Urgency)
- **Dominant**: High in Power and Legitimacy
- **Dangerous**: High in Power and Urgency
- **Dependent**: High in Legitimacy and Urgency
- **Dormant**: High in Power only
- **Discretionary**: High in Legitimacy only
- **Demanding**: High in Urgency only
- **Non-salient**: Low in all attributes

A score of 3 or above is considered "High" for each attribute.

## 🗃️ Data Storage

The app uses a SQLite database to store stakeholder information locally. The database file (`stakeholders.db`) is created in the same directory as the app.

## 🤝 Contributing

Contributions to improve the Stakeholder Salience Map App are welcome! Please feel free to submit issues, fork the repository and send pull requests!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📬 Citation / Contact

Cabayao, U. (2024). StakeholderSalienceMap [Web App]. Github. https://https://github.com/uscabayaosj/StakeholderSalienceMap/

If you have any questions, feel free to reach out to **Ulysses Cabayao, SJ** at [uscabayaosj@addu.edu.ph].

---

Created with ❤️ using Streamlit and Plotly.
