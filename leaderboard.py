def get_leaderboard(teams_list, games_list):
    # 1. Create a dictionary to store points: { "0": 0, "1": 0 ... }
    # We initialize every team with 0 points
    leaderboard = {team["id"]: 0 for team in teams_list}

    for game in games_list:
        t1_id = game["team1"]
        t2_id = game["team2"]
        
        # We need to check all 3 sets (score1, score2, score3)
        # Assuming a team wins the game if they win more sets
        t1_sets = 0
        t2_sets = 0

        for score_key in ["score1", "score2", "score3"]:
            score_str = game[score_key]
            if "x" in score_str:
                try:
                    s1, s2 = map(int, score_str.split("x"))
                    if s1 > s2:
                        t1_sets += 1
                    elif s2 > s1:
                        t2_sets += 1
                except ValueError:
                    continue # Skip if score is malformed

        # Determine game winner and award 1 point
        if t1_sets > t2_sets:
            leaderboard[t1_id] += 1
        elif t2_sets > t1_sets:
            leaderboard[t2_id] += 1

    # 2. Combine with team names and sort by points
    results = []
    for team in teams_list:
        results.append({
            "name": team["name"],
            "points": leaderboard.get(team["id"], 0)
        })

    # Sort: Highest points at the top
    results.sort(key=lambda x: x["points"], reverse=True)
    return results