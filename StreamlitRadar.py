import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy import stats
from mplsoccer import PyPizza, add_image
import streamlit as st
from PIL import Image

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv('Wyscout_League_Export 1-10-25.csv', encoding='latin-1')

    Top5EU = [
        'Spain La Liga 2024-25', 
        'England Premier League 2024-25',
        'Italy Serie A 2024-25', 
        'France Ligue 1 2024-25', 
        'Germany Bundesliga 2024-25'
    ]
    df = df[df['League'].isin(Top5EU)]
    df = df.dropna(subset=['Position']).reset_index(drop=True)

    # Main Position
    df['Main Position'] = df['Position'].apply(lambda x: x.split()[0].rstrip(','))
    positions = ['CF', 'LWF', 'RWF', 'RW', 'LW']
    df = df[df['Main Position'].isin(positions)]
    df = df[df["Minutes played"] >= 200]

    # Custom metrics
    df['Progressive passes'] = df['Accurate progressive passes, %'] /100 * df['Progressive passes per 90']
    df['Successful dribbles'] = df['Successful dribbles, %'] /100 * df['Dribbles per 90']
    df['Successful crosses'] = df['Accurate crosses, %'] /100 * df['Crosses per 90']

    df['90s'] = df['Minutes played'] / 90
    df['Successful passes per 90'] = df['Accurate passes, %'] /100 * df['Passes per 90']
    df['Completed passes'] =  df['Successful passes per 90'] * df['90s']
    df['100 passes'] = df['Completed passes'] / 100
    df['xA per 100 passes'] = df['xA'] / df['100 passes']

    df["Non-penalty xG"] = df["xG"]-df['Penalties taken']*0.76
    df['Received Passes'] =  df['Received passes per 90'] * df['90s']
    df['50 Received Passes'] = df['Received Passes'] / 50
    df['Non-Pen xG per 50 Received Passes'] = df['Non-penalty xG'] / df['50 Received Passes']
    df['Non-Pen xG per Received Pass'] = df['Non-penalty xG'] / df['Received Passes']

    df = df[['Player','League','Main Position','Minutes played',
             'Non-penalty xG', 'Non-penalty goals per 90', 
             'Non-Pen xG per Received Pass', 'Shots per 90', 'Shots on target, %', 
             'Goal conversion, %', 'Progressive runs per 90', 'Successful dribbles', 
             'Offensive duels per 90', 'Offensive duels won, %' , 'xA per 100 passes', 
             'Key passes per 90', 'Defensive duels per 90', 'Defensive duels won, %',
             'Aerial duels per 90', 'Aerial duels won, %']]

    df.columns = ['Player','League','Main Position','Minutes played',
                  'Non-penalty xG', 'Non-penalty goals\nper 90', 
                  'Non-Pen xG per\nReceived Pass', 'Shots per 90', 
                  'Shots on target, %', 'Goal conversion, %', 
                  'Progressive runs\nper 90', 'Successful dribbles', 
                  'Offensive duels\nper 90', 'Offensive duels\nwon, %' , 
                  'xA per 100 passes', 'Key passes per 90', 
                  'Defensive duels\nper 90','Defensive duels\nwon, %',  
                  'Aerial duels\nper 90', 'Aerial duels\nwon, %']

    return df

df = load_data()

# =========================
# STREAMLIT APP
# =========================
st.title("⚽ Player Pizza Plot Dashboard")

# Sidebar Filters
st.sidebar.header("⚙️ Filters")

# League filter
league_filter = st.sidebar.selectbox("Select League", sorted(df['League'].unique()))

# Filter df by league
df_league = df[df['League'] == league_filter]

# Position filter
position_filter = st.sidebar.selectbox("Select Position", sorted(df_league['Main Position'].unique()))

# Filter df by position
df_filtered = df_league[df_league['Main Position'] == position_filter]

# Player dropdown
player_name = st.sidebar.selectbox("Select a Player", sorted(df_filtered['Player'].unique()))

# Extract player values
params = list(df_filtered.columns)[4:]  # skip Player, League, Main Position, Minutes played
player_row = df_filtered.loc[df_filtered['Player'] == player_name].iloc[0]
player_values = player_row[4:].astype(float).values
minutes_played = int(player_row["Minutes played"])

# Percentile values
values = [
    math.floor(stats.percentileofscore(df_filtered[param].astype(float), player_values[i]))
    for i, param in enumerate(params)
]

# Colors
slice_colors = ["#44aa66"] * 6 + ["#f4c430"] * 6 + ["#367588"] * 4
text_colors = ["white"] * len(params)

# Instantiate Pizza with dark blue background
baker = PyPizza(
    params=params,
    background_color="#0A2D57",      # Dark blue background
    straight_line_color="#EBEBE9",
    straight_line_lw=1,
    last_circle_lw=0,
    other_circle_lw=0,
    inner_circle_size=5
)

fig, ax = baker.make_pizza(
    values,
    figsize=(10, 10),
    color_blank_space="same",
    slice_colors=slice_colors,
    value_colors=text_colors,
    value_bck_colors=slice_colors,
    blank_alpha=0.4,
    kwargs_slices=dict(edgecolor="#F2F2F2", zorder=2, linewidth=1),
    kwargs_params=dict(color="white", fontsize=11),   # white text
    kwargs_values=dict(
        color="white", fontsize=12,
        bbox=dict(edgecolor="white", facecolor="#0A2D57", 
                  boxstyle="round,pad=0.2", lw=1)
    )
)

# Titles
fig.text(0.515, 0.990, f"{player_name}", size=18, fontweight='bold',
         ha="center", color="white")

fig.text(0.515, 0.963, f"Percentile Rank vs {position_filter} | {league_filter}",
         size=14, ha="center", color="white")

# Legend (original position)
fig.text(0.35, 0.935, "Attacking     Possession     Defending", size=14,
         color="white")

fig.patches.extend([
    plt.Rectangle((0.32, 0.9275), 0.025, 0.021, fill=True, color="#44aa66",
                  transform=fig.transFigure, figure=fig),
    plt.Rectangle((0.445, 0.9275), 0.025, 0.021, fill=True, color="#f4c430",
                  transform=fig.transFigure, figure=fig),
    plt.Rectangle((0.582, 0.9275), 0.025, 0.021, fill=True, color="#367588",
                  transform=fig.transFigure, figure=fig),
])

# Minutes Played (Top Left Corner)
if minutes_played > 1500:
    min_color = "green"
elif minutes_played >= 800:
    min_color = "orange"
else:
    min_color = "red"

fig.text(0.05, 0.95, f"Minutes Played: {minutes_played}", size=12,
         ha="left", va="center", color=min_color,
         bbox=dict(facecolor="#0A2D57", edgecolor="white", boxstyle="round,pad=0.3"))

# =========================
# Add Logo (Top Right)
# =========================
logo = Image.open("Capture.png")  # uploaded logo
add_image(logo, fig, left=0.82, bottom=0.87, width=0.15, height=0.1)

# Display plot in Streamlit
st.pyplot(fig)




