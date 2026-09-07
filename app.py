import streamlit as st
import pandas as pd

from draw import generate_draw, assign_home_away, validate_draw


st.set_page_config(
    page_title="UEFA Champions League Draw",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ UEFA Champions League Draw Simulator")

st.write(
    "Generate a simulated UEFA Champions League league-phase draw."
)

# Load teams
df = pd.read_csv("teams.csv")

# Create dictionaries used by the draw
team_list = df["Team"].tolist()
country = dict(zip(df["Team"], df["Country"]))
pot = dict(zip(df["Team"], df["Pot"]))

# Generate draw button
if st.button("🎲 Generate Draw", type="primary"):

    edges = generate_draw()

    if edges is None:
        st.error("Could not create a valid draw. Please try again.")
    else:

        home, away = assign_home_away(edges)

        errors = validate_draw(edges, home, away)

        if errors:
            st.error("Draw has errors.")

            for error in errors:
                st.write(error)

        else:

            st.success("✅ Valid Champions League draw created!")

            st.write(f"**Total matches:** {len(edges)}")

            st.divider()

            # Show every team
            for team in team_list:

                st.subheader(team)

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 🏠 HOME")

                    for opponent in home[team]:
                        st.write(
                            f"Pot {pot[opponent]} — {opponent}"
                        )

                with col2:
                    st.markdown("### ✈️ AWAY")

                    for opponent in away[team]:
                        st.write(
                            f"Pot {pot[opponent]} — {opponent}"
                        )

                st.divider()
