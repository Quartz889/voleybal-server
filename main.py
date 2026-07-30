from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import auth
import table
import leaderboard

users = auth.begin("auth.txt")
teams = table.parse_teams("teams.txt")
games = table.parse_games("games.txt")

# Initialize the app
app = FastAPI()

origins = [
    "http://localhost:5173",  # Common port for Vue/Vite
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows everything (phone, laptop, etc.)
    allow_credentials=True,
    allow_methods=["*"], # Allows GET, POST, etc.
    allow_headers=["*"], # Allows all headers
)

#Reload all games in memory
@app.get("/root/refresh/games") # Removed {auth} from here
async def refreshGames(key: str): # Renamed variable to 'key'
    if auth.authRoot(users, key): # Use 'key' to check
        global games # Crucial: tells Python to update the global 'games' list
        games = table.parse_games("games.txt")
        return {"status": "success", "count": len(games)}
    else:
        auth.exceptionUnauthorised()

@app.post("/root/generate-robin")
async def start_season(key: str):
    if auth.authRoot(users, key):
        table.create_backup("games.txt")
        global games
        games = table.generate_robin("games.txt", teams)
        return {"status": "Robin Started"}

@app.post("/root/seed-playoffs")
async def seed_playoffs(key: str):
    if auth.authRoot(users, key):
        # Backup before we mess with the bracket
        table.create_backup("games.txt") 
        
        global games
        games = table.generate_playoffs("games.txt", teams, games)
        return {"status": "success"}

@app.post("/root/backup")
async def manual_backup(key: str):
    if auth.authRoot(users, key):
        table.create_backup("teams.txt")
        table.create_backup("games.txt")
        return {"status": "Backups created in /backups folder"}

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}

@app.get("/auth/{key}")
async def authenticate(key: str):
    if auth.authSuper(users, key):
        return {200}
    else:
        auth.exceptionUnauthorised()

@app.get("/game/set/{gameId}")
async def setGame(gameId: int, key: str):
    if auth.authSuper(users, key):
        return {"game": gameId, "result": 0}
    else:
        auth.exceptionUnauthorised()

class TeamCreate(BaseModel):
    name:str

@app.post("/teams")
async def addTeam(team_data: TeamCreate, key: str):
    if auth.authSuper(users, key):
        # Backup the teams list before adding
        table.create_backup("teams.txt")
        table.add_team("teams.txt", teams, team_data.name)
    else:
        auth.exceptionUnauthorised()

@app.get("/teams/get")
async def getTeams():
    return teams

@app.get("/teams/name/{id}")
async def getTeamNameById(id):
    return table.get_team_name(teams, id)

#Refresh leaderboard
@app.get("/leaderboard/get")
async def getLeaderboard():
    return leaderboard.get_leaderboard(teams, games)

#Get all games
# Get all games (Scores now always visible)
@app.get("/games/get/all")
async def get_games(key: str = None):
    # We keep the key check if you want to know who is looking, 
    # but we return the raw 'games' list without hiding anything.
    return games

#Get details of a specific game
@app.get("/games/get/game/{id}")
async def getGameById(id):
    return table.get_game_by_id(games, id)

#update games
class GameUpdate(BaseModel):
    id: str
    team1: str
    team2: str
    score1: str
    score2: str
    score3: str
    eval: str
    phase: str # Add this so the API accepts the phase from the frontend

@app.put("/games/update")
async def update_game(game: dict, key: str):
    # 1. Declare global FIRST
    global games 
    
    if key != "61": 
        return {"error": "Unauthorized"}
    
    # 2. Now you can safely use it
    success = table.edit_game("games.txt", games, game)
    
    if success:
        # Reload from file to ensure memory matches disk
        games = table.parse_games("games.txt")
        return {"status": "success"}
    
    return {"status": "error", "message": "Game not found"}