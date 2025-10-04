import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy import stats
import streamlit as st
from mplsoccer import PyPizza, add_image
import matplotlib.image as mpimg
import zipfile

# =========================
# LOAD DATA FOR PIZZA PLOT
# =========================
@st.cache_data
def load_data():
    zip_path = "Wyscout_League_Export 1-10-25.zip"
    csv_filename = "Wyscout_League_Export 1-10-25.csv"  # must match inside the zip

    with zipfile.ZipFile(zip_path, "r") as z:
        with z.open(csv_filename) as f:
            df = pd.read_csv(f, encoding="latin-1")

    # Filter Top 5 Leagues
    Top5EU = [
        "Spain La Liga 2024-25",
        "England Premier League 2024-25",
        "Italy Serie A 2024-25",
        "France Ligue 1 2024-25",
        "Germany Bundesliga 2024-25",
    ]
    df = df[df["League"].isin(Top5EU)]

    # Clean Position
    df = df.dropna(subset=["Position"]).reset_index(drop=True)
    df["Main Position"] = df["Position"].apply(lambda x: x.split()[0].rstrip(","))

    # Only CF / Wingers with minutes threshold
    positions = ["CF", "LWF", "RWF", "RW", "LW"]
    df = df[df["Main Position"].isin(positions)]
    df = df[df["Minutes played"] >= 800]

    # Custom metrics
    df["Progressive passes"] = df["Accurate progressive passes, %"] / 100 * df["Progressive passes per 90"]
    df["Successful dribbles"] = df["Successful dribbles, %"] / 100 * df["Dribbles per 90"]
    df["Successful crosses"] = df["Accurate crosses, %"] / 100 * df["Crosses per 90"]

    df["90s"] = df["Minutes played"] / 90
    df["Successful passes per 90"] = df["Accurate passes, %"] / 100 * df["Passes per 90"]
    df["Completed passes"] = df["Successful passes per 90"] * df["90s"]
    df["100 passes"] = df["Completed passes"] / 100
    df["xA per 100 passes"] = df["xA"] / df["100 passes"]

    df["Non-penalty xG"] = df["xG"] - df["Penalties taken"] * 0.76
    df["Received Passes"] = df["Received passes per 90"] * df["90s"]
    df["50 Received Passes"] = df["Received Passes"] / 50
    df["Non-Pen xG per 50 Received Passes"] = df["Non-penalty xG"] / df["50 Received Passes"]
    df["Non-Pen xG per Received Pass"] = df["Non-penalty xG"] / df["Received Passes"]

    df = df[
        [
            "Player",
            "League",
            "Main Position",
            "Non-penalty xG",
            "Non-penalty goals per 90",
            "Non-Pen xG per Received Pass",
            "Shots per 90",
            "Shots on target, %",
            "Goal conversion, %",
            "Progressive runs per 90",
            "Successful dribbles",
            "Offensive duels per 90",
            "Offensive duels won, %",
            "xA per 100 passes",
            "Key passes per 90",
            "Defensive duels per 90",
            "Defensive duels won, %",
            "Aerial duels per 90",
            "Aerial duels won, %",
        ]
    ]

    df.columns = [
        "Player",
        "League",
        "Main Position",
        "Non-penalty xG",
        "Non-penalty goals\nper 90",
        "Non-Pen xG per\nReceived Pass",
        "Shots per 90",
        "Shots on target, %",
        "Goal conversion, %",
        "Progressive runs\nper 90",
        "Successful dribbles",
        "Offensive duels\nper 90",
        "Offensive duels\nwon, %",
        "xA per 100 passes",
        "Key passes per 90",
        "Defensive duels\nper 90",
        "Defensive duels\nwon, %",
        "Aerial duels\nper 90",
        "Aerial duels\nwon, %",
    ]

    return df


# =========================
# LOAD DATA FOR RATINGS
# =========================
@st.cache_data
def load_excel(file_path):
    return pd.read_excel(file_path, sheet_name=None)  # dict {sheet_name: df}


# =========================
# STREAMLIT APP
# =========================
st.title("⚽ Expert GBE Hub Dashboard")

tab1, tab2 = st.tabs(["📊 Player Ratings", "🍕 Pizza Plot"])

# ========== TAB 1: Player Ratings ==========
with tab1:
    st.header("Player Ratings by Band & Role")

    file_path = "combined_band_sheets.xlsx"
    sheets_dict = load_excel(file_path)

    sheet_name = st.selectbox("Select Band (Sheet)", list(sheets_dict.keys()))
    df_band = sheets_dict[sheet_name]

    role_choice = st.selectbox(
        "Select Role",
        [
            "Complete CB",
            "Ball Playing CB",
            "Full Back (attacking)",
            "Full Back (defensive)",
            "Stopper",
            "Wide Central Defender",
            "Front-foot Agressive Ball Winner",
            "Deep-Lying Playmaker",
            "Runner",
            "Progressive Recycler",
            "Defensive Screen",
            "Defensive Winger",
            "Dribbling Winger",
            "Inside Forward",
            "Wide Direct Goalscorer",
            "False 9",
            "Pressing Forward",
            "Target Man",
            "Power Forward",
            "Pure Goalscorer",
        ],
    )

    if "Age" in df_band.columns:
        min_age = int(df_band["Age"].min())
        max_age = int(df_band["Age"].max())
        age_range = st.slider("Filter by Age", min_value=min_age, max_value=max_age, value=(min_age, max_age))
        df_band = df_band[(df_band["Age"] >= age_range[0]) & (df_band["Age"] <= age_range[1])]

    if "Main Position" in df_band.columns:
        positions = df_band["Main Position"].dropna().unique().tolist()
        selected_positions = st.multiselect("Filter by Main Position", options=positions, default=positions)
        df_band = df_band[df_band["Main Position"].isin(selected_positions)]

    top_n_choice = st.radio("Show Top:", options=["All", "Top 5", "Top 10"], index=0, horizontal=True)
    df_band = df_band.sort_values(by=role_choice, ascending=False)
    if top_n_choice == "Top 5":
        df_band = df_band.head(5)
    elif top_n_choice == "Top 10":
        df_band = df_band.head(10)

    columns_to_show = ["Player", "League", "Position", "Age", "Team", "Minutes played", role_choice]
    st.dataframe(df_band[columns_to_show])


# ========== TAB 2: Pizza Plot ==========
with tab2:
    st.header("Interactive Player Pizza Plot")

    df = load_data()

    league_filter = st.selectbox("Select League", sorted(df["League"].unique()))
    df_league = df[df["League"] == league_filter]
    player_name = st.selectbox("Select a Player", sorted(df_league["Player"].unique()))

    params = list(df_league.columns)[3:]
    player_row = df_league.loc[df_league["Player"] == player_name].iloc[0]
    player_values = player_row[3:].astype(float).values

    values = [
        math.floor(stats.percentileofscore(df_league[param].astype(float), player_values[i]))
        for i, param in enumerate(params)
    ]

    slice_colors = ["#44aa66"] * 6 + ["#f4c430"] * 6 + ["#367588"] * 4
    text_colors = ["#FFFFFF"] * len(params)

    baker = PyPizza(
        params=params,
        background_color="#0A2D57",
        straight_line_color="#FFFFFF",
        straight_line_lw=1,
        last_circle_lw=0,
        other_circle_lw=0,
        inner_circle_size=5,
    )

    fig, ax = baker.make_pizza(
        values,
        figsize=(10, 10),
        color_blank_space="same",
        slice_colors=slice_colors,
        value_colors=text_colors,
        value_bck_colors=slice_colors,
        blank_alpha=0.4,
        kwargs_slices=dict(edgecolor="#FFFFFF", zorder=2, linewidth=1),
        kwargs_params=dict(color="#FFFFFF", fontsize=11),
        kwargs_values=dict(
            color="#FFFFFF",
            fontsize=12,
            bbox=dict(edgecolor="#FFFFFF", facecolor="#0A2D57", boxstyle="round,pad=0.2", lw=1),
        ),
    )

    fig.text(0.515, 0.990, f"{player_name}", size=18, fontweight="bold", ha="center", color="#FFFFFF")
    fig.text(0.515, 0.963, f"Percentile Rank vs {league_filter}", size=14, ha="center", color="#FFFFFF")

    fig.text(0.35, 0.935, "Attacking     Possession     Defending", size=14, color="#FFFFFF")
    fig.patches.extend(
        [
            plt.Rectangle((0.32, 0.9275), 0.025, 0.021, fill=True, color="#44aa66", transform=fig.transFigure, figure=fig),
            plt.Rectangle((0.445, 0.9275), 0.025, 0.021, fill=True, color="#f4c430", transform=fig.transFigure, figure=fig),
            plt.Rectangle((0.582, 0.9275), 0.025, 0.021, fill=True, color="#367588", transform=fig.transFigure, figure=fig),
        ]
    )

    logo = mpimg.imread("Capture.png")
    add_image(logo, fig, left=0.82, bottom=0.02, width=0.15, height=0.08)

    plot_width = 80  # change manually here
    st.pyplot(fig, use_container_width=False, width=plot_width)








