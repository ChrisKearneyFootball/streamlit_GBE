import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy import stats
import streamlit as st
from mplsoccer import PyPizza, add_image
import matplotlib.image as mpimg

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_excel(file_path):
    return pd.read_excel(file_path, sheet_name=None)

# =========================
# ADD CUSTOM METRICS
# =========================
def add_custom_metrics(df):
    # Progressive passes
    if {'Accurate progressive passes, %', 'Progressive passes per 90'}.issubset(df.columns):
        df['Progressive passes'] = df['Accurate progressive passes, %'] / 100 * df['Progressive passes per 90']
        df = df.round({'Progressive passes': 2})
        
    # Successful dribbles
    if {'Successful dribbles, %', 'Dribbles per 90'}.issubset(df.columns):
        df['Successful dribbles'] = df['Successful dribbles, %'] / 100 * df['Dribbles per 90']
        df = df.round({'Successful dribbles': 2})
        
    # Successful crosses
    if {'Accurate crosses, %', 'Crosses per 90'}.issubset(df.columns):
        df['Successful crosses'] = df['Accurate crosses, %'] / 100 * df['Crosses per 90']
        df = df.round({'Successful crosses': 2})
        
    # xA per 100 passes
    if {'Minutes played', 'Accurate passes, %', 'Passes per 90', 'xA'}.issubset(df.columns):
        df['90s'] = df['Minutes played'] / 90
        df['Successful passes per 90'] = df['Accurate passes, %'] / 100 * df['Passes per 90']
        df['Completed passes'] = df['Successful passes per 90'] * df['90s']
        df['100 passes'] = df['Completed passes'] / 100
        df['xA per 100 passes'] = df['xA'] / df['100 passes']
        df = df.round({'xA per 100 passes': 2})
        
    # Non-penalty xG
    if {'xG', 'Penalties taken'}.issubset(df.columns):
        df['Non-penalty xG'] = df['xG'] - df['Penalties taken'] * 0.76
        
    # NPxG per Received Pass
    if {'Minutes played', 'Received passes per 90'}.issubset(df.columns) and 'Non-penalty xG' in df.columns:
        df['90s'] = df['Minutes played'] / 90
        df['Received Passes'] = df['Received passes per 90'] * df['90s']
        df['50 Received Passes'] = df['Received Passes'] / 50
        df['Non-Pen xG per 50 Received Passes'] = df['Non-penalty xG'] / df['50 Received Passes']
        df['Non-Pen xG per Received Pass'] = df['Non-penalty xG'] / df['Received Passes']
    
    # New metrics requested
    if {'Shots per 90', 'Shots on target, %'}.issubset(df.columns):
        df["Shots on Target per 90"] = df['Shots per 90'] * df["Shots on target, %"] / 100
        df = df.round({'Shots on Target per 90': 2})
        
    if {'Accurate passes to penalty area, %', 'Passes to penalty area per 90'}.issubset(df.columns):
        df["Succ Passes to pen area per 90"] = df["Accurate passes to penalty area, %"] * df["Passes to penalty area per 90"] / 100
        df = df.round({'Succ Passes to pen area per 90': 2})
        
    return df

# =========================
# POSITION GROUPS + METRICS
# =========================
POSITION_GROUPS = {
    "Forwards": ["CF", "RWF", "LWF"],
    "Wingers/AMs": ["AMF", "LAMF", "RAMF", "RW", "LW"],
    "CMs": ["RDMF", "LDMF", "DMF", "LCMF", "RCMF"],
    "FBs/WBs": ["RWB", "LWB", "LB", "RB"],
    "CBs": ["RCB", "LCB", "CB"],
}

METRICS = {
    "Forwards": [
        'Player','Non-penalty xG', 'Non-penalty goals per 90',
        'Non-Pen xG per Received Pass', 'Shots per 90', 'Shots on target, %',
        'Goal conversion, %', 'Progressive runs per 90', 'Successful dribbles',
        'Offensive duels per 90', 'Offensive duels won, %' , 'xA per 100 passes',
        'Key passes per 90', 'Defensive duels per 90', 'Defensive duels won, %',
        'Aerial duels per 90', 'Aerial duels won, %'
    ],
    "Wingers/AMs": [
        'Player','Non-penalty xG', 'Non-penalty goals per 90',
        'Non-Pen xG per Received Pass', 'Shots per 90', 'Shots on target, %',
        'Goal conversion, %', 'Progressive runs per 90', 'Successful dribbles',
        'Offensive duels per 90', 'Offensive duels won, %' , 'xA per 100 passes',
        'Key passes per 90', 'Defensive duels per 90', 'Defensive duels won, %',
        'Aerial duels per 90', 'Aerial duels won, %'
    ],
    "CMs": [
        'Player','Non-Penalty xG per 90','Progressive runs per 90',
        'Successful dribbles' ,'xA per 100 passes', 'Key passes per 90',
        'Accurate passes, %', 'Accurate forward passes, %', 'Forward passes per 90',
        'Progressive passes' , 'Deep completions per 90','Average pass length, m',
        'Defensive duels per 90','Defensive duels won, %', 'Aerial duels per 90',
        'Aerial duels won, %', 'PAdj Interceptions'
    ],
    "CBs": [
        'Player','Non-Penalty xG per 90','Progressive runs per 90',
        'Successful dribbles' ,'xA per 100 passes', 'Key passes per 90',
        'Accurate passes, %','Average pass length, m', 'Accurate forward passes, %',
        'Forward passes per 90','Progressive passes' , 'Deep completions per 90',
        'Shots blocked per 90', 'Defensive duels per 90', 'Defensive duels won, %',
        'Aerial duels per 90', 'Aerial duels won, %', 'PAdj Interceptions'
    ],
    "FBs/WBs": [
        'Player','Non-Penalty xG per 90','Shots on Target per 90','Progressive runs per 90',
        'Offensive duels won, %', 'Offensive duels per 90','Successful dribbles',
        'Touches in box per 90', 'xA per 100 passes','Key passes per 90',
        'Progressive passes','Accurate passes, %',"Succ Passes to pen area per 90",
        'Defensive duels per 90', 'Defensive duels won, %','Aerial duels per 90',
        'Aerial duels won, %', 'PAdj Interceptions'
    ]
}

# Custom metric names with line breaks to prevent overlap
CUSTOM_METRIC_NAMES = {
    'Non-penalty xG': 'Non-penalty\nxG',
    'Non-penalty goals per 90': 'Non-penalty\ngoals per 90',
    'Non-Pen xG per Received Pass': 'Non-Pen xG per\nReceived Pass',
    'Shots per 90': 'Shots\nper 90',
    'Shots on target, %': 'Shots on\ntarget, %',
    'Goal conversion, %': 'Goal\nconversion, %',
    'Progressive runs per 90': 'Progressive\nruns per 90',
    'Successful dribbles': 'Successful\ndribbles',
    'Offensive duels per 90': 'Offensive duels\nper 90',
    'Offensive duels won, %': 'Offensive duels\nwon, %',
    'xA per 100 passes': 'xA per\n100 passes',
    'Key passes per 90': 'Key passes\nper 90',
    'Defensive duels per 90': 'Defensive duels\nper 90',
    'Defensive duels won, %': 'Defensive duels\nwon, %',
    'Aerial duels per 90': 'Aerial duels\nper 90',
    'Aerial duels won, %': 'Aerial duels\nwon, %',
    'Accurate passes, %': 'Accurate\npasses, %',
    'Accurate forward passes, %': 'Accurate forward\npasses, %',
    'Forward passes per 90': 'Forward passes\nper 90',
    'Progressive passes': 'Progressive\npasses',
    'Deep completions per 90': 'Deep completions\nper 90',
    'Average pass length, m': 'Avg pass\nlength, m',
    'Shots blocked per 90': 'Shots blocked\nper 90',
    'PAdj Interceptions': 'PAdj\nInterceptions',
    'Shots on Target per 90': 'Shots on Target\nper 90',
    'Touches in box per 90': 'Touches in\nbox per 90',
    'Succ Passes to pen area per 90': 'Succ Passes to\npen area per 90'
}

# =========================
# STREAMLIT APP
# =========================
st.title("⚽ Expert GBE Hub Dashboard")
tab1, tab2 = st.tabs(["📊 Player Ratings", "🍕 Pizza Plot"])

# ========== TAB 1 ==========
with tab1:
    st.header("Player Ratings by Band & Role")
    file_path = "combined_band_sheets.xlsx"
    sheets_dict = load_excel(file_path)
    # Rename sheets to Band 1-6
    band_names = {f"Sheet{i}": f"Band {i}" for i in range(1, 7)}
    sheets_dict = {band_names.get(name, name): df for name, df in sheets_dict.items()}

    # Multi-select for bands
    sheet_names = st.multiselect("Select Bands", list(sheets_dict.keys()), default=list(sheets_dict.keys())[:1])
    
    # Combine selected bands' data for display
    df_combined = pd.concat([add_custom_metrics(sheets_dict[sheet_name].copy()) for sheet_name in sheet_names], 
                           keys=sheet_names, names=['Band', 'Index']).reset_index()

    # Team dropdown (does not affect calculations)
    if "Team" in df_combined.columns:
        teams = sorted(df_combined['Team'].dropna().astype(str).unique())
        selected_team = st.selectbox("Filter by Team (optional)", ["All"] + teams, key="tab1_team")
        if selected_team != "All":
            df_filtered = df_combined[df_combined["Team"].astype(str) == selected_team]
        else:
            df_filtered = df_combined.copy()
    else:
        df_filtered = df_combined.copy()

    # Player search bar
    search_query = st.text_input("Search Player", "", key="tab1_search")
    if search_query:
        df_filtered = df_filtered[df_filtered["Player"].astype(str).str.contains(search_query, case=False, na=False)]

    role_choice = st.selectbox("Select Role", [
        "Complete CB", "Ball Playing CB", "Full Back (attacking)", "Full Back (defensive)", 
        "Stopper", "Wide Central Defender", "Front-foot Agressive Ball Winner", 
        "Deep-Lying Playmaker", "Runner", "Progressive Recycler", "Defensive Screen", 
        "Defensive Winger", "Dribbling Winger", "Inside Forward", "Wide Direct Goalscorer", 
        "False 9", "Pressing Forward", "Target Man", "Power Forward", "Pure Goalscorer"
    ], key="tab1_role")

    # Age filter
    if "Age" in df_filtered.columns:
        min_age = int(df_filtered["Age"].min())
        max_age = int(df_filtered["Age"].max())
        age_range = st.slider("Filter by Age", min_value=min_age, max_value=max_age, value=(min_age, max_age), key="tab1_age")
        df_filtered = df_filtered[(df_filtered["Age"] >= age_range[0]) & (df_filtered["Age"] <= age_range[1])]

    # Position filter
    if "Main Position" in df_filtered.columns:
        positions = df_filtered["Main Position"].dropna().unique().tolist()
        selected_positions = st.multiselect("Filter by Main Position", options=positions, default=positions, key="tab1_position")
        df_filtered = df_filtered[df_filtered["Main Position"].isin(selected_positions)]

    # Top N filter
    top_n_choice = st.radio("Show Top:", options=["All", "Top 5", "Top 10"], index=0, horizontal=True, key="tab1_topn")
    df_filtered = df_filtered.sort_values(by=role_choice, ascending=False)
    if top_n_choice == "Top 5":
        df_filtered = df_filtered.head(5)
    elif top_n_choice == "Top 10":
        df_filtered = df_filtered.head(10)

    columns_to_show = ["Band", "Player", "League", "Position", "Age", "Team", "Minutes played", role_choice]
    st.dataframe(df_filtered[columns_to_show])

# ========== TAB 2 ==========
with tab2:
    st.header("Interactive Player Pizza Plot")
    sheet_name = st.selectbox("Select Band for Pizza Plot", list(sheets_dict.keys()), key="tab2_band")
    df = add_custom_metrics(sheets_dict[sheet_name].copy())

    # Position group
    selected_group = st.selectbox("Select Position Group", list(POSITION_GROUPS.keys()), key="tab2_group")
    group_positions = POSITION_GROUPS[selected_group]
    df_group = df[df["Main Position"].isin(group_positions)]  # Full group for percentiles

    # Team filter for dropdown only
    if "Team" in df_group.columns:
        teams = sorted(df_group['Team'].dropna().astype(str).unique())
        selected_team = st.selectbox("Filter by Team (dropdown only)", ["All"] + teams, key="tab2_team")
        if selected_team != "All":
            df_filtered = df_group[df_group["Team"].astype(str) == selected_team]
        else:
            df_filtered = df_group.copy()
    else:
        df_filtered = df_group.copy()

    # Player search bar
    search_query = st.text_input("Search Player", "", key="tab2_search")
    if search_query:
        df_filtered = df_filtered[df_filtered["Player"].astype(str).str.contains(search_query, case=False, na=False)]

    # Player selection
    player_name = st.selectbox("Select a Player", sorted(df_filtered['Player'].astype(str).unique()), key="tab2_player")

    # Metrics and params
    metrics = METRICS[selected_group]
    params = metrics[1:]
    # Apply custom names to params for display
    display_params = [CUSTOM_METRIC_NAMES.get(param, param) for param in params]

    player_row = df_group.loc[df_group['Player'] == player_name].iloc[0]
    player_values = player_row[params].astype(float).values

    # Percentiles
    values = [math.floor(stats.percentileofscore(df_group[param].astype(float), player_values[i])) for i, param in enumerate(params)]

    # Slice and text colors based on group
    if selected_group == "Forwards":
        slice_colors = ["#44aa66"] * 6 + ["#f4c430"] * 6 + ["#367588"] * 4
        text_colors = ["#000000"] * 16
    elif selected_group == "CMs":
        slice_colors = ["#44aa66"] * 3 + ["#f4c430"] * 8 + ["#367588"] * 5
        text_colors = ["#000000"] * 16
    elif selected_group == "FBs/WBs":
        slice_colors = ["#44aa66"] * 7 + ["#f4c430"] * 5 + ["#367588"] * 5
        text_colors = ["#000000"] * 17
    elif selected_group == "CBs":
        slice_colors = ["#44aa66"] * 3 + ["#f4c430"] * 8 + ["#367588"] * 6
        text_colors = ["#000000"] * 17
    elif selected_group == "Wingers/AMs":
        slice_colors = ["#44aa66"] * 6 + ["#f4c430"] * 6 + ["#367588"] * 4
        text_colors = ["#000000"] * 16
    else:
        slice_colors = ["#44aa66"] * len(params)
        text_colors = ["#000000"] * len(params)

    # Pizza chart
    baker = PyPizza(
        params=display_params,
        background_color="#0A2D57",
        straight_line_color="#FFFFFF",
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
        kwargs_slices=dict(edgecolor="#FFFFFF", zorder=2, linewidth=1),
        kwargs_params=dict(color="#FFFFFF", fontsize=11),
        kwargs_values=dict(color="#FFFFFF", fontsize=12,
                           bbox=dict(edgecolor="#FFFFFF", facecolor="#0A2D57", boxstyle="round,pad=0.2", lw=1))
    )

    # Titles
    fig.text(0.515, 0.9975, f"{player_name}", size=18, fontweight='bold', ha="center", color="#FFFFFF")
    team = player_row['Team'] if 'Team' in player_row else "Unknown Team"
    league = player_row['League'] if 'League' in player_row else "Unknown League"
    fig.text(0.515, 0.975, f"{team} - {league} | Percentile Rank vs {sheet_name} peers ({selected_group})", size=14, ha="center", color="#FFFFFF")

    # Top-left info
    info_texts = [f"Position: {player_row['Main Position']}", f"Minutes played: {player_row['Minutes played']}"]
    if 'Contract expires' in player_row:
        info_texts.append(f"Contract expires: {player_row['Contract expires']}")
    for i, txt in enumerate(info_texts):
        fig.text(0.02, 0.92 - i*0.025, txt, ha="left", color="#FFFFFF", fontsize=12)

    # Legend
    fig.text(0.35, 0.945, "Attacking     Possession     Defending", size=14, color="#FFFFFF")
    fig.patches.extend([
        plt.Rectangle((0.32, 0.9425), 0.025, 0.021, fill=True, color="#44aa66", transform=fig.transFigure, figure=fig),
        plt.Rectangle((0.445, 0.9425), 0.025, 0.021, fill=True, color="#f4c430", transform=fig.transFigure, figure=fig),
        plt.Rectangle((0.582, 0.9425), 0.025, 0.021, fill=True, color="#367588", transform=fig.transFigure, figure=fig),
    ])

    # Logo
    try:
        logo = mpimg.imread("Capture.png")
        add_image(logo, fig, left=0.82, bottom=0.02, width=0.15, height=0.08)
    except:
        pass

    st.pyplot(fig, use_container_width=False, width=80)








