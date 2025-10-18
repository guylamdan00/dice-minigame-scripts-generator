# ✅ Setup and Authentication
import gspread
import pandas as pd
import random
from google.auth import default
from google.colab import auth
from IPython.display import display, Javascript

auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

# ✅ Load the spreadsheet
#insert spreadsheet key below:
spreadsheet = gc.open_by_key('')

# ✅ Load boards and summary_table into DataFrames
boards_ws = spreadsheet.worksheet("boards")
summary_ws = spreadsheet.worksheet("summary_table")

boards_df = pd.DataFrame(boards_ws.get_values())
summary_df = pd.DataFrame(summary_ws.get_values())

boards_df.columns = boards_df.iloc[0]
boards_df = boards_df.drop(0).reset_index(drop=True)
boards_df.columns = boards_df.columns.str.lower()
boards_df['tile_reward'] = boards_df['tile_reward'].str.lower()

summary_df.columns = summary_df.iloc[0]
summary_df = summary_df.drop(0).reset_index(drop=True)
summary_df.columns = summary_df.columns.str.lower()
summary_df = summary_df[['board','total_throws','coinssi','gems','energy','chest','blue chest', 'bronze chest', 'purple chest','campaign chest','extra rolls','puzzle','magnifying glass','s progress','l progress','basic pack','silver pack','gold pack','epic pack']]

streak_limit = 1

def show_popup(message):
    display(Javascript(f'alert("{message}");'))

def validate_board_configurations(boards_df, summary_df):
    non_reward_columns = ["board", "total_throws", "num of throws vs expected",
                          "total points vs points level up", "throws grand total"]

    boards_df['board'] = boards_df['board'].astype(int)
    summary_df['board'] = summary_df['board'].astype(int)

    for _, row in summary_df.iterrows():
        board_id = int(row["board"])

        board_tiles = boards_df[boards_df["board"] == board_id]

        if board_tiles.empty:
            raise ValueError(f"Board '{board_id}' not found in boards_df. Available boards: {boards_df['board'].unique().tolist()}")

        tile_rewards = set(board_tiles['tile_reward'].dropna().unique())

        reward_targets = {}
        for col in summary_df.columns:
            if col in non_reward_columns:
                continue
            val = row[col]
            if pd.isnull(val) or str(val).strip() == '':
                continue
            try:
                numeric_val = int(float(val))
                if numeric_val > 0:
                    reward_targets[col] = numeric_val
            except ValueError:
                raise ValueError(f"Invalid numeric value '{val}' in column '{col}' for board '{board_id}'")

        missing_rewards = [reward for reward in reward_targets.keys()
                           if reward not in tile_rewards and reward not in ["s progress", "l progress"]]

        if missing_rewards:
           msg = f"Board '{board_id}' is missing rewards: {missing_rewards} in boards_df"
           show_popup(msg)
           raise ValueError(msg)

# ✅ Simulation function
def run_simulation(boards_df, summary_df, tile_count=24, start_tile=20, max_attempts=500000):
    results = []

    def parse_int(val):
        try:
            return int(float(val))
        except:
            return 0

    for _, row in summary_df.iterrows():
        board_id = int(row["board"])
        total_throws_target = parse_int(row["total_throws"])

        # Get board-specific rewards and level up points
        board_tiles = boards_df[boards_df["board"] == board_id]
        tile_rewards = {int(r["tile"]): r["tile_reward"] for _, r in board_tiles.iterrows()}
        if "points_to_level_up" not in board_tiles.columns or board_tiles["points_to_level_up"].isnull().all():
            raise ValueError(f"points_to_level_up is missing or NaN for board '{board_id}'.")

        points_to_level_up = parse_int(board_tiles["points_to_level_up"].iloc[0])

        # Extract item targets
        reward_targets = {}
        for col in summary_df.columns:
            if col not in ["board", "total_throws"] and parse_int(row[col]) > 0:
                reward_targets[col] = parse_int(row[col])

        # Compute bounds
        min_throws = total_throws_target
        max_throws = total_throws_target

        found = False
        for _ in range(max_attempts):
            num_throws = random.randint(min_throws, max_throws)
            pos = start_tile
            progress = 0
            collected = {}
            throws = []

            for t in range(num_throws - 1):
                valid_rolls = []
                for d in range(1, 7):
                    if len(throws) >= streak_limit and all(prev == d for prev in throws[-streak_limit:]):
                        continue

                    new_pos = (pos + d) % tile_count
                    reward = tile_rewards.get(new_pos, "")
                    if reward in ["s progress", "l progress"]:
                        pts = 1 if reward == "s progress" else 3
                        if (
                            progress + pts < points_to_level_up and
                            collected.get(reward, 0) < reward_targets.get(reward, 0)
                        ):
                            valid_rolls.append(d)
                    elif reward in reward_targets:
                        if collected.get(reward, 0) < reward_targets[reward]:
                            valid_rolls.append(d)

                if not valid_rolls:
                    break

                roll = random.choice(valid_rolls)
                throws.append(roll)
                pos = (pos + roll) % tile_count
                reward = tile_rewards.get(pos, "")

                if reward == "s progress":
                    progress += 1
                    collected["s progress"] = collected.get("s progress", 0) + 1
                elif reward == "l progress":
                    progress += 3
                    collected["l progress"] = collected.get("l progress", 0) + 1
                elif reward:
                    collected[reward] = collected.get(reward, 0) + 1

            # Final throw to level up
            remaining_points = points_to_level_up - progress
            if remaining_points not in [1, 3]:
                continue

            final_found = False
            for d in range(1, 7):
                if len(throws) >= streak_limit and all(prev == d for prev in throws[-streak_limit:]):
                    continue
                final_pos = (pos + d) % tile_count
                final_reward = tile_rewards.get(final_pos, "")
                final_pts = 1 if final_reward == "s progress" else 3 if final_reward == "l progress" else 0

                if final_pts == remaining_points:
                    # Collect final reward
                    if final_reward == "s progress":
                        progress += 1
                        collected["s progress"] = collected.get("s progress", 0) + 1
                    elif final_reward == "l progress":
                        progress += 3
                        collected["l progress"] = collected.get("l progress", 0) + 1
                    elif final_reward:
                        collected[final_reward] = collected.get(final_reward, 0) + 1

                    # Check if all rewards match targets
                    if all(collected.get(k, 0) == v for k, v in reward_targets.items()):
                        throws.append(d)
                        results.append({"board": board_id, "throw_sequence": ", ".join(map(str, throws))})
                        found = True
                        final_found = True
                        break

            if found and final_found:
                break

        if not found:
            results.append({"board": board_id, "throw_sequence": "Failed to match criteria"})

    return pd.DataFrame(results)

validate_board_configurations(boards_df, summary_df)

# ✅ Run the simulation
result_df = run_simulation(boards_df, summary_df)


# Write results to a new sheet
if "sim_output" in [ws.title for ws in spreadsheet.worksheets()]:
    spreadsheet.del_worksheet(spreadsheet.worksheet("sim_output"))
sim_ws = spreadsheet.add_worksheet(title="sim_output", rows="100", cols="2")

sim_ws.append_row(["board", "throw_sequence"])
for _, row in result_df.iterrows():
    sim_ws.append_row([row["board"], row["throw_sequence"]])

result_df.head()
