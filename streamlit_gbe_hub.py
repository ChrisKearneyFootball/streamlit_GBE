import streamlit as st 
import pandas as pd

st.title("Expert GBE Hub Player Ratings")

st.subheader("Filter to Band and Age")

# Load all sheets into DataFrames (serializable)
@st.cache_data
def load_excel(file_path):
    return pd.read_excel(file_path, sheet_name=None)  # returns a dict {sheet_name: df}

# Path to your Excel file
file_path = "combined_band_sheets.xlsx"
sheets_dict = load_excel(file_path)

# Dropdown to choose sheet
sheet_name = st.selectbox("Select Band (Sheet)", list(sheets_dict.keys()))

# Get the chosen sheet
df = sheets_dict[sheet_name]

# Dropdown to choose column
role_choice = st.selectbox("Select Role", ["Complete CB", "Ball Playing CB", "Full Back (attacking)", "Full Back (defensive)", "Stopper", "Wide Central Defender", "Front-foot Agressive Ball Winner", "Deep-Lying Playmaker", "Runner", "Progressive Recycler", "Defensive Screen", "Defensive Winger", "Dribbling Winger", "Inside Forward", "Wide Direct Goalscorer", "False 9", "Pressing Forward", "Target Man", "Power Forward", "Pure Goalscorer"])

# --- Age Filter ---
if "Age" in df.columns:
    min_age = int(df["Age"].min())
    max_age = int(df["Age"].max())
    age_range = st.slider(
        "Filter by Age",
        min_value=min_age,
        max_value=max_age,
        value=(min_age, max_age)
    )
    df = df[(df["Age"] >= age_range[0]) & (df["Age"] <= age_range[1])]

    # --- Main Position Filter ---
if "Main Position" in df.columns:
    positions = df["Main Position"].dropna().unique().tolist()
    selected_positions = st.multiselect(
        "Filter by Main Position",
        options=positions,
        default=positions  # show all by default
    )
    df = df[df["Main Position"].isin(selected_positions)]

    # --- Top N Filter ---
top_n_choice = st.radio(
    "Show Top:",
    options=["All", "Top 5", "Top 10"],
    index=0,
    horizontal=True
)

# Sort by selected role column
df = df.sort_values(by=role_choice, ascending=False)

if top_n_choice == "Top 5":
    df = df.head(5)
elif top_n_choice == "Top 10":
    df = df.head(10)

# Select only the columns we want to show
columns_to_show = ["Player", "League", "Position", "Age", "Team", "Minutes played", role_choice]

# Display the dataframe
st.dataframe(df[columns_to_show])






