import streamlit as st
from statsbombpy import sb
import pandas as pd
from mplsoccer import Pitch, VerticalPitch
from main import progressive_stats, final_third_stats, pass_stats, passes, pass_network, defensive_stats, \
    possession_stats, shot_accuracy

st.set_page_config(
    page_title="Football Analytics",
    layout="wide")

# Custom style
st.markdown("""
<style>

    .main {
        background-color: #f7f8fa;}

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;}

    h1 {
        font-size: 42px !important;
        font-weight: 700 !important;}

    h2 {
        font-size: 26px !important;}

    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;}

</style>
""", unsafe_allow_html=True)


# Load data
match_id = 4020846

events = sb.events(match_id=match_id)

shots = events[
    (events["type"] == "Shot") &
    (events["shot_type"] == "Open Play")].copy()

shots["on_target"] = shots["shot_outcome"].isin(
    ["Goal", "Saved"])

team_stats = shots.groupby("team").agg(
    shots=("id", "count"),
    shots_on_target=("on_target", "sum"),
    xg=("shot_statsbomb_xg", "sum"),
    goals=("shot_outcome", lambda x: (x == "Goal").sum())).reset_index()

team_stats["xg"] = team_stats["xg"].round(2)


st.title("England Women's vs Spain Women's")

st.caption(
    "Football Match Analytics • StatsBomb Event Data")

st.divider()

# Score
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    st.markdown("### England Women's")

with col2:
    st.markdown("## 1 — 1")
    st.markdown("### 3 — 1 pens")

with col3:
    st.markdown("### Spain Women's")


st.divider()

st.subheader("Match Overview")

england = team_stats[
    team_stats["team"] == "England Women's"].iloc[0]

spain = team_stats[
    team_stats["team"] == "Spain Women's"].iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "England xG",
        england["xg"]
    )

with col2:
    st.metric(
        "Spain xG",
        spain["xg"]
    )

with col3:
    st.metric(
        "England Shots",
        england["shots"]
    )

with col4:
    st.metric(
        "Spain Shots",
        spain["shots"]
    )


st.divider()


# xG chart
st.subheader("Expected Goals")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.bar_chart(
        team_stats.set_index("team")["xg"])

# shot map
st.subheader("Shot Map")

col1, col2, col3 = st.columns([1, 2, 1])


with col2:

    pitch = VerticalPitch(
        pitch_type="statsbomb",
        pitch_color="#123524",
        line_color="white",
        half=True
    )

    fig, ax = pitch.draw(figsize=(5, 4))

    for _, shot in shots.iterrows():

        x = shot["location"][0]
        y = shot["location"][1]

        if shot["team"] == "England Women's":
            colour = "#2f3282"
        else:
            colour = "#87313f"

        xg = shot["shot_statsbomb_xg"]

        if pd.isna(xg):
            xg = 0.05

        pitch.scatter(
            x,
            y,
            ax=ax,
            s=xg * 1500,
            color=colour,
            alpha=0.8
        )

    # Legend
    ax.scatter([], [], color="#2f3282", s=80, label="England")
    ax.scatter([], [], color="#87313f", s=80, label="Spain")

    legend = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 0.08),
        ncol=2,
        fontsize=9,
        frameon=True
    )

    legend.get_frame().set_facecolor("#ffffff")
    legend.get_frame().set_alpha(0.6)
    legend.get_frame().set_edgecolor("none")

    fig.patch.set_alpha(0)

    st.pyplot(fig)


# passing comparison
passing_comparison = pass_stats.merge(
    progressive_stats,
    on="team")

passing_comparison = passing_comparison.merge(
    final_third_stats,
    on="team")

passing_comparison["pass_completion_%"] = (
    passing_comparison["completed_passes"]
    / passing_comparison["total_passes"] * 100).round(1)

st.subheader("Passing Comparison")

st.dataframe(
    passing_comparison[
        [
            "team",
            "total_passes",
            "completed_passes",
            "pass_completion_%",
            "progressive_passes",
            "final_third_entries"
        ]],hide_index=True,use_container_width=True)


# passing networks
st.subheader("Passing Networks")

col1, col2 = st.columns(2)

for col, team, colour in [
    (col1, "England Women's", "#2f3282"),
    (col2, "Spain Women's", "#87313f")
]:

    with col:

        team_passes = passes[
            passes["team"] == team
        ].dropna(subset=["pass_recipient"])

        team_network = pass_network[
            pass_network["team"] == team]

        player_positions = team_passes.groupby("player")["location"].apply(
            lambda x: (
                x.apply(lambda p: p[0]).mean(),
                x.apply(lambda p: p[1]).mean()
            ))

        pitch = Pitch(
            pitch_type="statsbomb",
            pitch_color="#123524",
            line_color="black")

        fig, ax = pitch.draw(figsize=(5, 4))

        # Passing lines
        for _, row in team_network.iterrows():

            passer = row["player"]
            receiver = row["pass_recipient"]

            if passer not in player_positions.index:
                continue

            if receiver not in player_positions.index:
                continue

            x1, y1 = player_positions[passer]
            x2, y2 = player_positions[receiver]

            pitch.lines(
                x1, y1, x2, y2,
                ax=ax,
                color=colour,
                alpha=0.35,
                linewidth=row["passes"] / 3)

        # Players
        for player, position in player_positions.items():

            x, y = position

            pitch.scatter(
                x, y,
                ax=ax,
                s=350,
                color=colour,
                edgecolors="black")

            ax.text(
                x, y,
                player.split()[-1],
                ha="center",
                va="center",
                fontsize=8,
                color="white")

        ax.set_title(
            team,
            fontsize=14,
            fontweight="bold",
            color="white")

        fig.patch.set_alpha(0)

        st.pyplot(fig)

# possession comparison
st.subheader("Possession")

col1, col2 = st.columns(2)

for col, team in zip([col1, col2], possession_stats["team"]):

    with col:
        value = possession_stats[
            possession_stats["team"] == team
        ]["ball_receipts"].iloc[0]

        st.metric(team, value)

# defensive comparison
st.subheader("Defensive Comparison")

st.dataframe(
    defensive_stats[
        [
            "team",
            "pressures",
            "duels",
            "carries"
        ]],
    hide_index=True,
    use_container_width=True)

st.subheader("Attacking Comparison")

attacking_comparison = team_stats[
    [
        "team",
        "shots",
        "shots_on_target",
        "xg",
        "goals"]].copy()

attacking_comparison["shot_accuracy_%"] = shot_accuracy

attacking_comparison["xg_per_shot"] = (
    attacking_comparison["xg"]
    / attacking_comparison["shots"]).round(2)

attacking_comparison["goals_minus_xg"] = (
    attacking_comparison["goals"]
    - attacking_comparison["xg"]).round(2)

st.dataframe(
    attacking_comparison,
    hide_index=True,
    use_container_width=True)

