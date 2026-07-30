import itertools

def parse_teams(path):
    teams = []
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if not line:                 # skip empty lines
                continue
            parts = line.split("=")
            if len(parts) != 3:          # skip lines that don't have exactly 3 fields
                print(f"WARNING: skipping invalid line: {line}")
                continue
            teams.append({"id": parts[0], "name": parts[1], "eval": parts[2]})
    return teams

def parse_games(path):
    games = []
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if not line: continue
            p = line.split(",")
            # Ensure we read all 8 columns
            games.append({
                "id": p[0], "team1": p[1], "team2": p[2],
                "score1": p[3], "score2": p[4], "score3": p[5],
                "eval": p[6], 
                "phase": p[7] if len(p) > 7 else "robin"
            })
    return games

def add_team(path, teams_list, team_name):
    # 1. Calculate the next ID based on the current list
    if teams_list:
        # Get the ID of the last dictionary in the list and add 1
        last_id = int(teams_list[-1]["id"])
        next_id = last_id + 1
    else:
        next_id = 0

    # 2. Append to the file (minimal I/O)
    with open(path, "a") as file:
        file.write(f"\n{next_id}={team_name}=0")

    # 3. Update the list in-place so it's ready for the next call
    new_team = {"id": str(next_id), "name": team_name}
    teams_list.append(new_team)

    return new_team

def get_team_name(teams, id):
    for team in teams:
        if team["id"] == id:
            return team["name"]

def get_game_by_id(games, id):
    for game in games:
        if game["id"] == id:
            return game

def edit_game(path, games_list, updated_game):
    found = False
    for i, game in enumerate(games_list):
        if game["id"] == updated_game["id"]:
            games_list[i] = updated_game
            found = True
            break
    
    if not found: return False

    with open(path, "w") as file:
        for g in games_list:
            # Explicitly write the 8th column: phase
            line = f"{g['id']},{g['team1']},{g['team2']},{g['score1']},{g['score2']},{g['score3']},{g['eval']},{g.get('phase', 'robin')}\n"
            file.write(line)
    return True

import itertools

def _save_to_file(path, games):
    with open(path, "w") as f:
        for g in games:
            # Use .get() with defaults to avoid any missing key errors
            gid = g.get('id', '')
            t1 = g.get('team1', 'TBD')
            t2 = g.get('team2', 'TBD')
            s1 = g.get('score1', '')
            s2 = g.get('score2', '')
            s3 = g.get('score3', '')
            ev = g.get('eval', '')
            ph = g.get('phase', 'robin')
            
            # This writes the 8 columns your backend expects
            f.write(f"{gid},{t1},{t2},{s1},{s2},{s3},{ev},{ph}\n")

import random

def generate_robin(path, teams_list):
    """
    Generates a balanced Round Robin schedule where teams 
    get breaks between rounds using the Circle Method.
    """
    if len(teams_list) < 2:
        return []

    team_ids = [str(t["id"]) for t in teams_list]
    
    # If odd number of teams, add a 'Bye' to make it even
    if len(team_ids) % 2 != 0:
        team_ids.append(None)

    random.shuffle(team_ids) # Randomize starting order
    
    num_rounds = len(team_ids) - 1
    half_way = len(team_ids) // 2
    
    new_games = []
    game_id = 0

    for _ in range(num_rounds):
        # The "Circle" pairings
        for i in range(half_way):
            t1 = team_ids[i]
            t2 = team_ids[-(i + 1)]
            
            # Only record the game if it's not a 'Bye'
            if t1 is not None and t2 is not None:
                new_games.append({
                    "id": str(game_id),
                    "team1": t1,
                    "team2": t2,
                    "score1": "",
                    "score2": "",
                    "score3": "",
                    "eval": f"Round {game_id // half_way + 1}",
                    "phase": "robin"
                })
                game_id += 1
        
        # Rotate the list: keep the first element, move the rest
        team_ids = [team_ids[0]] + [team_ids[-1]] + team_ids[1:-1]

    # Save to file
    _save_to_file(path, new_games)
    return new_games

import math

import math

def generate_playoffs(path, teams_list, current_games):
    print("--- Playoff Seeding Started ---")

    n = len(teams_list)
    if n < 2:
        return current_games

    bracket_size = 2 ** math.ceil(math.log2(n))

    # 1. Standings from robin phase
    standings = {str(t["id"]): 0 for t in teams_list}
    for g in current_games:
        if (g.get("phase") == "robin" or not g.get("phase")) and "x" in str(g.get("score1", "")):
            try:
                s1, s2 = map(int, g["score1"].split('x'))
                if s1 > s2: standings[str(g["team1"])] += 1
                elif s2 > s1: standings[str(g["team2"])] += 1
            except: continue

    sorted_ids = sorted(standings, key=standings.get, reverse=True)
    seeds = sorted_ids + ["BYE"] * (bracket_size - len(sorted_ids))

    # 2. Map existing playoff games
    playoff_map = {
        g.get("eval", "").lower().strip(): g
        for g in current_games if g.get("phase") == "playoffs"
    }

    def get_winner(label):
        target = next((g for lbl, g in playoff_map.items() if label.lower() in lbl), None)
        if not target or "x" not in str(target.get("score1", "")):
            return "TBD"
        try:
            s1, s2 = map(int, target["score1"].split('x'))
            return str(target["team1"]) if s1 > s2 else str(target["team2"])
        except:
            return "TBD"

    def get_loser(label):
        target = next((g for lbl, g in playoff_map.items() if label.lower() in lbl), None)
        if not target or "x" not in str(target.get("score1", "")):
            return "TBD"
        try:
            s1, s2 = map(int, target["score1"].split('x'))
            return str(target["team2"]) if s1 > s2 else str(target["team1"])
        except:
            return "TBD"

    # 3. Main bracket
    ROUND_NAMES = {
        2:  ["Finalas"],
        4:  ["Pusfinalis {i}", "Finalas"],
        8:  ["Ketvirtfinalis {i}", "Pusfinalis {i}", "Finalas"],
        16: ["1/8 Final {i}", "Ketvirtfinalis {i}", "Pusfinalis {i}", "Finalas"],
        32: ["1/16 Final {i}", "1/8 Final {i}", "Ketvirtfinalis {i}", "Pusfinalis {i}", "Finalas"],
    }
    round_templates = ROUND_NAMES.get(
        bracket_size,
        [f"Raundas {r+1} {{i}}" for r in range(int(math.log2(bracket_size)) - 1)] + ["Finalas"]
    )

    playoff_structure = []
    round_game_objects = []
    classification_games = []   # will be inserted before the final

    # First round
    first_round_label = round_templates[0]
    first_round_games = []
    lo, hi = 0, bracket_size - 1
    for i in range(bracket_size // 2):
        t1, t2 = seeds[lo], seeds[hi]
        lo += 1; hi -= 1
        label = first_round_label.replace("{i}", str(i+1)) if "{i}" in first_round_label else first_round_label
        first_round_games.append({"eval": label, "t1": t1, "t2": t2})
    playoff_structure.extend(first_round_games)
    round_game_objects.append(first_round_games)

    prev_labels = [g["eval"] for g in first_round_games]
    semifinal_labels = []

    for round_idx in range(1, len(round_templates)):
        label_template = round_templates[round_idx]
        next_labels = []
        round_games = []
        for i in range(len(prev_labels) // 2):
            w1 = get_winner(prev_labels[i*2])
            w2 = get_winner(prev_labels[i*2+1])
            label = label_template.replace("{i}", str(i+1)) if "{i}" in label_template else label_template
            game = {"eval": label, "t1": w1, "t2": w2}
            round_games.append(game)
            playoff_structure.append(game)
            next_labels.append(label)
        round_game_objects.append(round_games)

        if round_idx == len(round_templates) - 2:
            semifinal_labels = next_labels.copy()
        prev_labels = next_labels

    # Third place match (insert before the final)
    if semifinal_labels and len(semifinal_labels) >= 2:
        third_place_game = {
            "eval": "Dėl 3 vietos",
            "t1": get_loser(semifinal_labels[0]),
            "t2": get_loser(semifinal_labels[1])
        }
        playoff_structure.insert(-1, third_place_game)

    # --- Helper to add a full classification bracket for a group of losers ---
    def add_class_bracket(losers, rank_start, is_last_pool=False):
        L = len(losers)
        if L < 2:
            return
        prefix = f"Kova dėl {rank_start}-{rank_start + L - 1} vietų"

        # Mini round templates
        MINI = {
            2: ["Finalas"],
            4: ["Pusfinalis {i}", "Finalas"],
            8: ["Ketvirtfinalis {i}", "Pusfinalis {i}", "Finalas"],
            16: ["1/8 Final {i}", "Ketvirtfinalis {i}", "Pusfinalis {i}", "Finalas"],
        }
        mini = MINI.get(L, [f"R{x+1} {{i}}" for x in range(int(math.log2(L))-1)] + ["Finalas"])

        # First round (semi‑finals for L=4, quarter‑finals for L=8, etc.)
        lbl0 = mini[0]
        cur_lbls = []
        for i in range(0, L, 2):
            lbl = lbl0.replace("{i}", str(i//2+1)) if "{i}" in lbl0 else lbl0
            full = f"{prefix} {lbl}"
            classification_games.append({"eval": full, "t1": losers[i], "t2": losers[i+1]})
            cur_lbls.append(full)

        # For L=4, the first round IS the semi‑final → capture its labels for the 3rd place game
        semi_lbls = []
        if L == 4:
            semi_lbls = cur_lbls.copy()
        elif L >= 8:
            # semi‑final labels will be captured inside the loop (the round before the final)
            pass

        # Subsequent rounds
        for cr in range(1, len(mini)):
            tmpl = mini[cr]
            nxt = []
            for i in range(len(cur_lbls)//2):
                w1 = get_winner(cur_lbls[i*2])
                w2 = get_winner(cur_lbls[i*2+1])
                lbl = tmpl.replace("{i}", str(i+1)) if "{i}" in tmpl else tmpl
                full = f"{prefix} {lbl}"
                classification_games.append({"eval": full, "t1": w1, "t2": w2})
                nxt.append(full)
            # If this was the round that created the semi‑finals (second‑last round), save them
            if cr == len(mini) - 2:   # semi‑final round
                semi_lbls = nxt.copy()
            cur_lbls = nxt

        # Third place / Last place match
        if L == 2:
            # The only game already determines last place; rename it
            if is_last_pool:
                classification_games[-1]["eval"] = "Dėl paskutinės vietos"
        elif L >= 4 and semi_lbls and len(semi_lbls) == 2:
            l1 = get_loser(semi_lbls[0])
            l2 = get_loser(semi_lbls[1])
            if is_last_pool:
                third_lbl = "Dėl paskutinės vietos"
            else:
                third_lbl = f"{prefix} Dėl {rank_start+2} vietos"
            classification_games.append({"eval": third_lbl, "t1": l1, "t2": l2})

    # --- Generate classification brackets ---
    num_rounds = len(round_templates)
    pools = []
    for r in range(num_rounds - 2):
        games = round_game_objects[r]
        losers = []
        for g in games:
            if g["t1"] != "BYE" and g["t2"] != "BYE":
                losers.append(get_loser(g["eval"]))
        if len(losers) >= 2:
            rank_start = 2 ** (num_rounds - r - 1) + 1
            pools.append((rank_start, losers))
    # Sort pools so that the one with highest rank_start (lowest places) is last
    pools.sort(key=lambda x: x[0], reverse=True)
    for idx, (rank_start, losers) in enumerate(pools):
        is_last = (idx == 0)   # first in sorted list is highest rank_start => last place pool
        add_class_bracket(losers, rank_start, is_last_pool=is_last)

    # Insert all classification games BEFORE the final
    playoff_structure[-1:-1] = classification_games

    # 4. Merge with existing games
    new_list = [g for g in current_games if g.get("phase") != "playoffs"]
    start_id = len(new_list)

    for i, m in enumerate(playoff_structure):
        existing = next((g for lbl, g in playoff_map.items() if m["eval"].lower() in lbl), {})
        t1, t2 = m["t1"], m["t2"]
        if t1 == "BYE":
            t1 = t2 = t2
        elif t2 == "BYE":
            t2 = t1

        new_list.append({
            "id":     str(start_id + i),
            "team1":  str(t1),
            "team2":  str(t2),
            "score1": existing.get("score1", ""),
            "score2": existing.get("score2", ""),
            "score3": existing.get("score3", ""),
            "eval":   m["eval"],
            "phase":  "playoffs"
        })

    _save_to_file(path, new_list)
    print(f"--- Playoff Seeding Complete ({len(playoff_structure)} games, bracket size {bracket_size}) ---")
    return new_list

import shutil
import os
from datetime import datetime

def create_backup(filename):
    """Copies the given file to a 'backups' folder with a timestamp."""
    if not os.path.exists("backups"):
        os.makedirs("backups")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backups/{timestamp}_{filename}"
    
    try:
        shutil.copy2(filename, backup_name)
        print(f"Backup created: {backup_name}")
    except FileNotFoundError:
        print(f"Error: {filename} not found, no backup created.")
