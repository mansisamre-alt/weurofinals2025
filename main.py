from statsbombpy import sb
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from matplotlib.lines import Line2D

# Load match data

competitions = sb.competitions()

# Finding competition and season IDs
# print(
#     competitions[
#         ["competition_id", "competition_name", "season_id", "season_name"]
#     ]
# )

matches = sb.matches(
    competition_id=53,
    season_id=315
)

# Finding match ID
# print(
#     matches[
#         [
#             "match_id",
#             "match_date",
#             "home_team",
#             "away_team",
#             "home_score",
#             "away_score",
#             "competition_stage"
#         ]
#     ]
# )


# Load events

match_id = 4020846

events = sb.events(match_id=match_id)

print("Events:", events.shape)


# Load shots
shots = events[events["type"] == "Shot"].copy()

print("Total shots including penalties:", len(shots))

# Only open-play shots
non_penalty_shots = shots[
    shots["shot_type"] == "Open Play"].copy()

print("Open-play shots:", len(non_penalty_shots))

print("\nShot types:")
print(shots["shot_type"].value_counts())


# Shot on target
non_penalty_shots["on_target"] = (
    non_penalty_shots["shot_outcome"].isin(["Goal", "Saved"]))


# Team stats
team_stats = non_penalty_shots.groupby("team").agg(
    shots=("id", "count"),
    shots_on_target=("on_target", "sum"),
    xg=("shot_statsbomb_xg", "sum"),
    goals=("shot_outcome", lambda x: (x == "Goal").sum())
).reset_index()

team_stats["xg"] = team_stats["xg"].round(2)

team_stats["xg_per_shot"] = (
    team_stats["xg"] / team_stats["shots"]).round(2)

team_stats["goals_minus_xg"] = (
    team_stats["goals"] - team_stats["xg"]).round(2)

team_stats["xg"] = team_stats["xg"].round(2)

shot_accuracy = (
    team_stats["shots_on_target"]
    / team_stats["shots"] * 100).round(1)

print("TEAM STATISTICS")
print(team_stats.to_string(index=False))


# Shot map
pitch = Pitch(pitch_type="statsbomb")

fig, ax = pitch.draw(figsize=(12, 8))

for _, shot in non_penalty_shots.iterrows():

    x = shot["location"][0]
    y = shot["location"][1]

    if shot["team"] == "England Women's":
        colour = "blue"
    else:
        colour = "red"

    # Use xG to control dot size
    xg = shot["shot_statsbomb_xg"]

    if pd.isna(xg):
        xg = 0.05

    pitch.scatter(
        x,
        y,
        ax=ax,
        s=xg * 1500,
        color=colour,
        alpha=0.7
    )

ax.set_title("England Women's vs Spain Women's — Open Play Shot Map",fontsize=20)

plt.show()


# Team xG bar chart
xg_data = team_stats.set_index("team")["xg"]

xg_data.plot(kind="bar")

plt.title("Expected Goals (xG) — Open Play")
plt.ylabel("xG")
plt.xlabel("Team")

plt.show()


# Goals
goals = non_penalty_shots[
    non_penalty_shots["shot_outcome"] == "Goal"]

goals_by_team = goals.groupby("team").size()

print("GOALS")
print(goals_by_team)


# Player stats
player_stats = non_penalty_shots.groupby(
    ["team", "player"]).agg(
    shots=("id", "count"),
    xg=("shot_statsbomb_xg", "sum"),
    goals=("shot_outcome", lambda x: (x == "Goal").sum())).reset_index()


player_stats["xg_per_shot"] = (
    player_stats["xg"] / player_stats["shots"]).round(2)

player_stats["xg"] = player_stats["xg"].round(2)

player_stats["goals_minus_xg"] = (
    player_stats["goals"] - player_stats["xg"]).round(2)


player_stats = player_stats.sort_values("xg", ascending=False)

print("PLAYER STATISTICS")
print(player_stats.to_string(index=False))


# Top players by xG
top_players = player_stats.head(5)

print("TOP 5 PLAYERS BY xG")
print(top_players.to_string(index=False))


top_players.plot(
    x="player",
    y="xg",
    kind="bar")

plt.title("Top 5 Players by Open-Play xG")
plt.ylabel("Expected Goals (xG)")
plt.xlabel("Player")

plt.show()


# Finishing performance
print("FINISHING PERFORMANCE")
print(
    player_stats[
        [
            "team",
            "player",
            "goals",
            "xg",
            "goals_minus_xg"
        ]
    ].to_string(index=False))


# Creating passing dataframe
passes = events[events["type"] == "Pass"].copy()

pass_stats = passes.groupby("team")

total_passes = pass_stats["id"].count()
completed_passes = pass_stats["pass_outcome"].apply(lambda x: x.isna().sum())

pass_stats = pd.DataFrame({
    "total_passes": total_passes,
    "completed_passes": completed_passes})

pass_stats = pass_stats.reset_index()

print(pass_stats)
pass_stats["pass_completion_%"] = (
    pass_stats["completed_passes"] /
    pass_stats["total_passes"] * 100).round(1)

print("\nPassing statistics:")
print(pass_stats.to_string(index=False))

print(passes[["team", "player", "location", "pass_end_location"]].head())

passes["progression"] = (
    passes["pass_end_location"].apply(lambda x: x[0])
    - passes["location"].apply(lambda x: x[0]))


# Passing map
first_half = passes[passes["period"] == 1]
second_half = passes[passes["period"] == 2]

fig, axes = plt.subplots(1, 2, figsize=(20, 8))

pitch = Pitch(
    pitch_type="statsbomb",
    pitch_color="#f5f5f5",
    line_color="#333333")


# Draw both pitches
pitch.draw(ax=axes[0])
pitch.draw(ax=axes[1])

# Attack direction
axes[0].text(
    52, -5,
    "England attacking →",
    ha="center",
    fontsize=14,
    fontweight="bold")

axes[0].text(
    52, 73,
    "← Spain attacking",
    ha="center",
    fontsize=14,
    fontweight="bold")

axes[1].text(
    52, -5,
    "← England attacking",
    ha="center",
    fontsize=14,
    fontweight="bold")

axes[1].text(
    52, 73,
    "Spain attacking →",
    ha="center",
    fontsize=14,
    fontweight="bold")

# First half
for _, pass_event in first_half.iterrows():

    start_x = pass_event["location"][0]
    start_y = pass_event["location"][1]

    end_x = pass_event["pass_end_location"][0]
    end_y = pass_event["pass_end_location"][1]

    if pass_event["team"] == "England Women's":
        colour = "blue"
    else:
        colour = "red"

    pitch.arrows(
        start_x,
        start_y,
        end_x,
        end_y,
        ax=axes[0],
        color=colour,
        width=1,
        headwidth=3,
        headlength=4,
        alpha=0.15)


# Second half
for _, pass_event in second_half.iterrows():

    start_x = pass_event["location"][0]
    start_y = pass_event["location"][1]

    end_x = pass_event["pass_end_location"][0]
    end_y = pass_event["pass_end_location"][1]

    if pass_event["team"] == "England Women's":
        colour = "blue"
    else:
        colour = "red"

    pitch.arrows(
        start_x,
        start_y,
        end_x,
        end_y,
        ax=axes[1],
        color=colour,
        width=1,
        headwidth=3,
        headlength=4,
        alpha=0.15)


# Titles
axes[0].set_title(
    "First Half",
    fontsize=20,
    fontweight="bold")

axes[1].set_title(
    "Second Half",
    fontsize=20,
    fontweight="bold")

fig.suptitle(
    "England Women's vs Spain Women's — Passing Map",
    fontsize=24,
    fontweight="bold")


legend = [
    Line2D([0], [0], color="blue", lw=3, label="England"),
    Line2D([0], [0], color="red", lw=3, label="Spain")]

axes[0].legend(handles=legend, loc="upper left")

plt.tight_layout()
plt.show()


# Progressive passes
passes["progression"] = (
    passes["pass_end_location"].apply(lambda x: x[0])
    - passes["location"].apply(lambda x: x[0]))

progressive_passes = passes[passes["progression"] > 10]

progressive_stats = progressive_passes.groupby("team").agg(
    progressive_passes=("id", "count")).reset_index()

print("PROGRESSIVE PASSES")
print(progressive_stats.to_string(index=False))

# Final third entries
final_third_entries = passes[
    passes["pass_end_location"].apply(lambda x: x[0] >= 80)]

final_third_stats = final_third_entries.groupby("team").agg(
    final_third_entries=("id", "count")).reset_index()

print("FINAL-THIRD ENTRIES")
print(final_third_stats.to_string(index=False))


# Pressure on opponents
pressures = events[
    events["type"] == "Pressure"].copy()

pressure_stats = pressures.groupby("team").agg(pressures=("id", "count")).reset_index()

print("PRESSURES")
print(pressure_stats.to_string(index=False))

# Pass network
passes_with_receiver = passes.dropna(subset=["pass_recipient"])

pass_network = passes_with_receiver.groupby(["team", "player", "pass_recipient"]).size()

pass_network = pass_network.reset_index(name="passes")

print("PASS NETWORK")
print(pass_network.to_string(index=False))


# England womens passing network
team = "England Women's"

team_passes = passes[passes["team"] == team].dropna(subset=["pass_recipient"])

# Average player positions
player_positions = team_passes.groupby("player")["location"].apply(
    lambda x: (
        x.apply(lambda p: p[0]).mean(),
        x.apply(lambda p: p[1]).mean()
    ))

pitch = Pitch(
    pitch_type="statsbomb",
    pitch_color="#f5f5f5",
    line_color="#333333")

fig, ax = pitch.draw(figsize=(12, 8))


# Passing connections
for _, row in pass_network[pass_network["team"] == team].iterrows():

    passer = row["player"]
    receiver = row["pass_recipient"]

    if passer not in player_positions.index:
        continue

    if receiver not in player_positions.index:
        continue

    x1, y1 = player_positions[passer]
    x2, y2 = player_positions[receiver]

    pitch.lines(
        x1,
        y1,
        x2,
        y2,
        ax=ax,
        color="blue",
        alpha=0.3,
        linewidth=row["passes"] / 3)


# Players
for player, position in player_positions.items():

    x, y = position

    pitch.scatter(
        x,
        y,
        ax=ax,
        s=500,
        color="blue",
        edgecolors="black")

    ax.text(
        x,
        y,
        player.split()[-1],
        ha="center",
        va="center",
        fontsize=9,
        color="white")


ax.set_title(
    "England Women's Passing Network",
    fontsize=20,
    fontweight="bold")

plt.show()

# Spain womens passing network
team = "Spain Women's"

team_passes = passes[passes["team"] == team].dropna(subset=["pass_recipient"])

# Average player positions
player_positions = team_passes.groupby("player")["location"].apply(
    lambda x: (
        x.apply(lambda p: p[0]).mean(),
        x.apply(lambda p: p[1]).mean()
    ))

pitch = Pitch(
    pitch_type="statsbomb",
    pitch_color="#f5f5f5",
    line_color="#333333")

fig, ax = pitch.draw(figsize=(12, 8))

# Passing connections
for _, row in pass_network[pass_network["team"] == team].iterrows():

    passer = row["player"]
    receiver = row["pass_recipient"]

    if passer not in player_positions.index:
        continue

    if receiver not in player_positions.index:
        continue

    x1, y1 = player_positions[passer]
    x2, y2 = player_positions[receiver]

    pitch.lines(
        x1,
        y1,
        x2,
        y2,
        ax=ax,
        color="red",
        alpha=0.3,
        linewidth=row["passes"] / 3)

# Passing comparison
passing_comparison = passes.groupby("team").agg(
    total_passes=("id", "count"),
    completed_passes=("pass_outcome", lambda x: x.isna().sum())).reset_index()

passing_comparison["pass_completion_%"] = (
    passing_comparison["completed_passes"]
    / passing_comparison["total_passes"] * 100).round(1)

passing_comparison["progressive_passes"] = (
    passes["progression"] > 10).groupby(passes["team"]).sum().values

passing_comparison["final_third_entries"] = (
    passes["pass_end_location"]
    .apply(lambda x: x[0] >= 80)
    .groupby(passes["team"]).sum().values)

print("\nPassing Comparison:")
print(passing_comparison)


# Players
for player, position in player_positions.items():

    x, y = position

    pitch.scatter(
        x,
        y,
        ax=ax,
        s=500,
        color="red",
        edgecolors="black")

    ax.text(
        x,
        y,
        player.split()[-1],
        ha="center",
        va="center",
        fontsize=9,
        color="white")


ax.set_title(
    "Spain Women's Passing Network",
    fontsize=20,
    fontweight="bold")

plt.show()


# Possession by half
possession = events[events["type"] == "Ball Receipt*"].copy()

possession_stats = possession.groupby(["period", "team"]).size().reset_index(name="ball_receipts")

print("POSSESSION BY HALF")
print(possession_stats.to_string(index=False))


# Duels
duels = events[events["type"] == "Duel"].copy()

duel_stats = duels.groupby("team").agg(duels=("id", "count")).reset_index()

print("DUELS")
print(duel_stats.to_string(index=False))

# Defensive comparison
carries = events[
    events["type"] == "Carry"].copy()

carry_stats = carries.groupby("team").agg(
    carries=("id", "count")).reset_index()

defensive_stats = pressures.groupby("team").agg(
    pressures=("id", "count")).reset_index()

defensive_stats = defensive_stats.merge(
    duel_stats,
    on="team",
    how="left")

defensive_stats = defensive_stats.merge(
    carry_stats,
    on="team",
    how="left")

print("\nDefensive Comparison:")
print(defensive_stats)

possession_stats = possession.groupby("team").size().reset_index(
    name="ball_receipts")

print("\nPossession Comparison:")
print(possession_stats)


# # dropna - removes rows or columns that contain missing values (NaN).
# # lambda - creates a small, one-line function without giving it a name.
# # isna - checks whether a value is missing (NaN).