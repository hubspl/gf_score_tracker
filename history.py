import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

def app():
    # Load secrets and authenticate
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gspread"], scope)
    gc = gspread.authorize(credentials)

    # Open the sheet
    sh = gc.open("godfather_game_history")
    worksheet = sh.sheet1

    # Load game history
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)

    # Get all unique GameIDs, sorted descending (latest first)
    game_ids = sorted(df["GameID"].unique(), reverse=True)

    st.title("Game History")
    st.divider()

    for game_id in game_ids:
        game_df = df[df["GameID"] == game_id].copy()
        game_date = game_df["Date"].iloc[0]

        # Sort by Total score descending
        top_players = game_df.sort_values(by="Total", ascending=False).head(3)
        medals = ["🥇", "🥈", "🥉"]

        # Build top summary safely
        top_summary = " ".join(
            f"{medals[i]} {row['Player']} ({row['Total']})"
            for i, (_, row) in enumerate(top_players.iterrows())
            if i < len(medals)
        )

        with st.expander(f"🕹️ Game {game_id} · {top_summary}", expanded=False):
            
            # Display the full table without GameID and Date
            display_df = game_df.drop(columns=["GameID", "Date"])
            st.dataframe(display_df.reset_index(drop=True), hide_index=True)

