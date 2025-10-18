🎲 Dice Scripts Generator

This tool was built to eliminate the tedious and error-prone process of manually creating dice throw sequences to FoF's dice mini game. It simulates optimized throw paths based on board configurations and reward targets, saving time and reducing mistakes in reward testing or campaign scripting.

📌 Features

✅ Automatically connects to Google Sheets

✅ Loads board tiles and reward targets into pandas DataFrames

✅ Validates that boards support the defined reward goals

✅ Simulates dice throws under game constraints (e.g. no streaks)

✅ Finds sequences that match exact reward and progression requirements

✅ Outputs results to a new worksheet for easy copy-paste or QA

⚙️ Setup and Authentication

Designed for Google Colab, with seamless authentication via your Google account:

import gspread
from google.colab import auth
from google.auth import default

auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

📄 Spreadsheet Structure

This tool reads from a spreadsheet with the following key sheets:

boards: Defines tile layout and rewards for each board.

summary_table: Specifies per-board reward targets, total throws, and progression requirements.

After cleaning, both are loaded into lowercase DataFrames, and validated to ensure all rewards are covered.

✅ Configuration Validation

Before simulation:

Each board in summary_table must have a corresponding layout in boards

All required rewards (except progress) must appear in that board

Missing points_to_level_up values are flagged immediately

🧠 Simulation Logic

The simulation:

Tries thousands of throw sequences (default: up to 500,000 per board)

Tracks position, progress, rewards, and streak rules

Ensures final throw completes the level-up with exact remaining points

Stops early on success and records the sequence

Example output:

{
  "board": 12,
  "throw_sequence": "4, 6, 2, 5, 3, 1, ..."
}


If no valid sequence is found within the limit, it records a failure.

📤 Results Output

The tool creates (or replaces) a sheet called sim_output with:

board	throw_sequence
1	2, 6, 3, 1, 5, 2, 3, 6, 4, 1 ...
2	Failed to match criteria
🛠️ Parameters You Can Tweak
Parameter	Description
tile_count	Default 24 tiles in a board
start_tile	Default starting index (0-based)
streak_limit	Prevents repeating same dice value
max_attempts	Upper limit for retry attempts
🚫 Eliminating Manual Work

Previously, generating throw scripts was a manual, repetitive task—requiring test runs, guesswork, and manual writing. This tool automates the entire process by:

Running up to 500k simulations per board

Matching precise reward distributions

Returning ready-to-use throw sequences

📎 Dependencies

Install these Python packages if needed:

!pip install gspread pandas

🤝 License & Contributions

Internal use only. For improvements or feedback, contact guylamdan00@gmail.com
