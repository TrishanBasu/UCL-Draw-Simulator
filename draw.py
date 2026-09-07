import random
import pandas as pd
from collections import defaultdict

# Load the CSV file
df = pd.read_csv("teams.csv")
team_list = df["Team"].tolist()

# -----------------------------
# BASIC DATA FROM YOUR DATAFRAME
# -----------------------------

country = dict(zip(df["Team"], df["Country"]))
pot = dict(zip(df["Team"], df["Pot"]))

pots = {
    p: df[df["Pot"] == p]["Team"].tolist()
    for p in range(1, 5)
}

# -----------------------------
# CHECK IF TWO TEAMS CAN PLAY
# -----------------------------

def can_add(a, b, edges, country_count):

    # Team cannot play itself
    if a == b:
        return False

    # Same country not allowed
    if country[a] == country[b]:
        return False

    # Duplicate match not allowed
    edge = tuple(sorted((a, b)))

    if edge in edges:
        return False

    # Maximum 2 opponents from another country
    if country_count[a][country[b]] >= 2:
        return False

    if country_count[b][country[a]] >= 2:
        return False

    return True


# -----------------------------
# ADD / REMOVE MATCH
# -----------------------------

def add_edge(a, b, edges, country_count):

    edge = tuple(sorted((a, b)))

    edges.add(edge)

    country_count[a][country[b]] += 1
    country_count[b][country[a]] += 1


def remove_edge(a, b, edges, country_count):

    edge = tuple(sorted((a, b)))

    edges.remove(edge)

    country_count[a][country[b]] -= 1
    country_count[b][country[a]] -= 1


# -----------------------------
# SAME POT DRAW
# -----------------------------

def create_same_pot_cycle(nodes, edges, country_count):

    start = random.choice(nodes)

    path = [start]
    used = {start}

    def search():

        # All 9 teams used
        if len(path) == len(nodes):

            # Last team must also be able to play first team
            return can_add(
                path[-1],
                path[0],
                edges,
                country_count
            )

        current = path[-1]

        candidates = []

        for opponent in nodes:

            if opponent in used:
                continue

            if can_add(
                current,
                opponent,
                edges,
                country_count
            ):
                candidates.append(opponent)

        random.shuffle(candidates)

        for opponent in candidates:

            path.append(opponent)
            used.add(opponent)

            if search():
                return True

            used.remove(opponent)
            path.pop()

        return False

    if not search():
        return None

    cycle_edges = []

    for i in range(len(path)):

        a = path[i]
        b = path[(i + 1) % len(path)]

        cycle_edges.append((a, b))

    return cycle_edges


# -----------------------------
# PERFECT MATCHING BETWEEN POTS
# -----------------------------

def perfect_matching(
    left,
    right,
    edges,
    country_count,
    banned_edges=None
):

    if banned_edges is None:
        banned_edges = set()

    unmatched = set(right)

    matches = []

    left_order = list(left)

    def search(position):

        if position == len(left_order):
            return True

        # Find the team with the fewest legal choices
        best_position = None
        best_candidates = None

        for j in range(position, len(left_order)):

            team = left_order[j]

            candidates = []

            for opponent in unmatched:

                edge = tuple(sorted((team, opponent)))

                if edge in banned_edges:
                    continue

                if can_add(
                    team,
                    opponent,
                    edges,
                    country_count
                ):
                    candidates.append(opponent)

            if (
                best_candidates is None
                or len(candidates) < len(best_candidates)
            ):

                best_candidates = candidates
                best_position = j

        if not best_candidates:
            return False

        # Move most difficult team first
        left_order[position], left_order[best_position] = (
            left_order[best_position],
            left_order[position]
        )

        team = left_order[position]

        candidates = []

        for opponent in unmatched:

            edge = tuple(sorted((team, opponent)))

            if edge in banned_edges:
                continue

            if can_add(
                team,
                opponent,
                edges,
                country_count
            ):
                candidates.append(opponent)

        random.shuffle(candidates)

        for opponent in candidates:

            matches.append((team, opponent))

            unmatched.remove(opponent)

            add_edge(
                team,
                opponent,
                edges,
                country_count
            )

            if search(position + 1):
                return True

            remove_edge(
                team,
                opponent,
                edges,
                country_count
            )

            unmatched.add(opponent)

            matches.pop()

        return False

    if search(0):
        return matches.copy()

    return None


# -----------------------------
# GENERATE FULL DRAW
# -----------------------------

def generate_draw(max_attempts=500):

    for attempt in range(max_attempts):

        edges = set()

        country_count = {
            team: defaultdict(int)
            for team in team_list
        }

        success = True

        # -----------------------------------
        # STEP 1: 2 opponents from own pot
        # -----------------------------------

        for p in range(1, 5):

            cycle = create_same_pot_cycle(
                pots[p],
                edges,
                country_count
            )

            if cycle is None:

                success = False
                break

            for a, b in cycle:

                add_edge(
                    a,
                    b,
                    edges,
                    country_count
                )

        if not success:
            continue

        # -----------------------------------
        # STEP 2: Other pots
        # -----------------------------------

        pot_pairs = [
            (1, 2),
            (1, 3),
            (1, 4),
            (2, 3),
            (2, 4),
            (3, 4)
        ]

        random.shuffle(pot_pairs)

        for pot_a, pot_b in pot_pairs:

            # First opponent from this pot
            matching1 = perfect_matching(
                pots[pot_a],
                pots[pot_b],
                edges,
                country_count
            )

            if matching1 is None:

                success = False
                break

            # Prevent duplicate opponent
            banned = {
                tuple(sorted(match))
                for match in matching1
            }

            # Second opponent from this pot
            matching2 = perfect_matching(
                pots[pot_a],
                pots[pot_b],
                edges,
                country_count,
                banned
            )

            if matching2 is None:

                success = False
                break

        # 36 teams × 8 matches / 2
        # = 144 total matches

        if success and len(edges) == 144:

            return edges

    return None


# -----------------------------
# HOME / AWAY ALLOCATION
# -----------------------------

def assign_home_away(edges):

    home = {
        team: []
        for team in team_list
    }

    away = {
        team: []
        for team in team_list
    }

    # Treat every pot combination separately
    for p in range(1, 5):

        for q in range(p, 5):

            sub_edges = []

            for a, b in edges:

                pot_a = pot[a]
                pot_b = pot[b]

                if p == q:

                    if pot_a == p and pot_b == p:
                        sub_edges.append((a, b))

                else:

                    if {pot_a, pot_b} == {p, q}:
                        sub_edges.append((a, b))

            # Build connections
            adjacency = defaultdict(list)

            for a, b in sub_edges:

                adjacency[a].append(b)
                adjacency[b].append(a)

            unvisited = set(adjacency.keys())

            # Every group forms a cycle
            while unvisited:

                start = next(iter(unvisited))

                cycle = [start]

                previous = None
                current = start

                while True:

                    neighbours = adjacency[current]

                    if neighbours[0] != previous:
                        next_team = neighbours[0]
                    else:
                        next_team = neighbours[1]

                    if next_team == start:
                        break

                    cycle.append(next_team)

                    previous = current
                    current = next_team

                # Orient the cycle
                # A -> B means A is HOME
                for i in range(len(cycle)):

                    home_team = cycle[i]

                    away_team = cycle[
                        (i + 1) % len(cycle)
                    ]

                    home[home_team].append(away_team)
                    away[away_team].append(home_team)

                for team in cycle:
                    unvisited.discard(team)

    return home, away


# -----------------------------
# VALIDATOR
# -----------------------------

def validate_draw(edges, home, away):

    opponents = {
        team: set()
        for team in team_list
    }

    for a, b in edges:

        opponents[a].add(b)
        opponents[b].add(a)

    errors = []

    for team in team_list:

        # Must have 8 opponents
        if len(opponents[team]) != 8:
            errors.append(
                f"{team}: does not have 8 opponents"
            )

        # Must have 4 home
        if len(home[team]) != 4:
            errors.append(
                f"{team}: does not have 4 home games"
            )

        # Must have 4 away
        if len(away[team]) != 4:
            errors.append(
                f"{team}: does not have 4 away games"
            )

        # Check every pot
        for p in range(1, 5):

            pot_opponents = [
                x
                for x in opponents[team]
                if pot[x] == p
            ]

            if len(pot_opponents) != 2:

                errors.append(
                    f"{team}: wrong number from Pot {p}"
                )

            home_from_pot = [
                x
                for x in home[team]
                if pot[x] == p
            ]

            away_from_pot = [
                x
                for x in away[team]
                if pot[x] == p
            ]

            if len(home_from_pot) != 1:

                errors.append(
                    f"{team}: needs 1 HOME game from Pot {p}"
                )

            if len(away_from_pot) != 1:

                errors.append(
                    f"{team}: needs 1 AWAY game from Pot {p}"
                )

        # Same-country check
        for opponent in opponents[team]:

            if country[team] == country[opponent]:

                errors.append(
                    f"{team} plays same-country team {opponent}"
                )

        # Maximum 2 opponents from any country
        counts = defaultdict(int)

        for opponent in opponents[team]:

            counts[country[opponent]] += 1

        for opponent_country, count in counts.items():

            if count > 2:

                errors.append(
                    f"{team} has more than 2 opponents "
                    f"from {opponent_country}"
                )

    return errors


# -----------------------------
# RUN THE DRAW
# -----------------------------

edges = generate_draw()

if edges is None:

    print("❌ Could not create draw. Run the cell again.")

else:

    home, away = assign_home_away(edges)

    errors = validate_draw(
        edges,
        home,
        away
    )

    if len(errors) == 0:

        print("✅ VALID CHAMPIONS LEAGUE DRAW CREATED!")
        print()
        print("Total matches:", len(edges))
        print("All 36 teams have:")
        print("✓ 8 opponents")
        print("✓ 2 opponents from every pot")
        print("✓ 4 home games")
        print("✓ 4 away games")
        print("✓ 1 home + 1 away from every pot")
        print("✓ No same-country opponents")
        print("✓ Maximum 2 opponents from another country")

    else:

        print("❌ Draw has errors:")

        for error in errors:
            print(error)
