import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def app():
    st.set_page_config(layout="wide")

    # Set up credentials from st.secrets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
    gc = gspread.authorize(credentials)

    # Open the Google Sheet
    sh = gc.open("godfather_game_history")
    worksheet = sh.sheet1

    # Convert to DataFrame
    def load_game_history():
        records = worksheet.get_all_records()
        return pd.DataFrame(records)

    # Sumbmit game to Google Sheets
    def submit_game_to_sheet(game_data):
        # Get all rows to determine the latest GameID
        existing_rows = worksheet.get_all_records()

        # Determine the next GameID
        if existing_rows:
            latest_game_id = max(row.get("GameID", 0) for row in existing_rows)
        else:
            latest_game_id = 0

        next_game_id = latest_game_id + 1

        column_order = ["Player", "$1", "$2", "$3", "$5", "Green", "Yellow", "Grey", "Blue", "Domination", "Total", "GameID", "Date"]

        for row in game_data:
            row["GameID"] = next_game_id
            row["Date"] = datetime.now().isoformat()
            values = [row.get(col, "") for col in column_order]
            worksheet.append_row(values)



    st.title("Add Game")

    if "game_history" not in st.session_state:
        st.session_state.game_history = pd.DataFrame()


    # Session state initialization
    if 'players' not in st.session_state:
        st.session_state.players = []

    if 'scores' not in st.session_state:
        st.session_state.scores = {}

    # Add new player

    st.subheader("Add Players")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_player = st.text_input("Player name")

    if st.button("Add Player") and new_player:
        if new_player not in st.session_state.players:
            st.session_state.players.append(new_player)
            st.session_state.scores[new_player] = {}
        else:
            st.warning("Player already added.")

    if st.button("Reset All Players"):
        st.session_state.players = []
        st.session_state.scores = {}

    # Define score categories
    categories = ["$1", 
                "$2", 
                "$3", 
                "$5", 
                "Green", 
                "Yellow", 
                "Grey", 
                "Blue", 
                "Domination"
    ]

    # Score input section
    st.subheader("Enter Scores")

    for player in st.session_state.players:
        with st.expander(f"🧑 {player}", expanded=True):

            # Create one column per category dynamically
            cols = st.columns(len(categories))
            for i, category in enumerate(categories):
                key = f"{player}_{category}"
                default = st.session_state.scores[player].get(category, 0)
                with cols[i]:
                    st.session_state.scores[player][category] = st.number_input(
                        label=f"{category}",
                        key=key,
                        value=default,
                        step=1
                    )

    # Create DataFrame
    if st.session_state.players:
        data = []

        # Step 1: Gather raw scores
        player_raw = {}
        for player in st.session_state.players:
            player_raw[player] = st.session_state.scores[player]

        # Step 2: Determine top players for each color category
        bonus_categories = ["Green", "Yellow", "Grey", "Blue"]
        bonus_winners = {color: [] for color in bonus_categories}

        for color in bonus_categories:
            # Find max value in this color
            max_value = max([player_raw[p].get(color, 0) for p in player_raw])
            # Find all players with that max value
            for p in player_raw:
                if player_raw[p].get(color, 0) == max_value and max_value > 0:
                    bonus_winners[color].append(p)

        # Step 3: Compute score rows
        for player in st.session_state.players:
            scores = player_raw[player]
            row = {"Player": player}
            for cat in categories:
                row[cat] = scores.get(cat, 0)

            # Apply custom base formula
            base_score = (
                scores.get("$1", 0) * 1 +
                scores.get("$2", 0) * 2 +
                scores.get("$3", 0) * 3 +
                scores.get("$5", 0) * 5 +
                scores.get("Domination", 0) * 5
            )

            # Step 4: Add 5 points for each color category won
            color_bonus = sum([
                5 if player in bonus_winners[color] else 0
                for color in bonus_categories
            ])

            row["Total"] = base_score + color_bonus
            data.append(row)

        # Step 5: Display table
        df = pd.DataFrame(data)
        df = df.sort_values(by="Total", ascending=False)
        st.subheader("Leaderboard")
        st.dataframe(df.reset_index(drop=True), use_container_width=True, hide_index=True)

    if st.button("✅ Submit Game"):
        df_current_game = pd.DataFrame(data)  # your current game scores
        submit_game_to_sheet(df_current_game.to_dict(orient="records"))
        st.success("Game submitted to Google Sheets!")
