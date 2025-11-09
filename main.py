from fastapi import FastAPI, HTTPException
from nba_api.stats.endpoints import scoreboardv2, playergamelog, commonplayerinfo
from nba_api.stats.static import players, teams
from datetime import datetime

app = FastAPI(title="NBA API")

@app.get("/")
def root():
    return {"status": "online", "service": "NBA API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/players/search")
def search_players(name: str):
    results = players.find_players_by_full_name(name)
    return results if results else []

@app.get("/player/{player_id}/info")
def player_info(player_id: int):
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        return info.get_normalized_dict()
    except:
        raise HTTPException(status_code=404, detail="Player not found")

@app.get("/player/{player_id}/gamelog")
def player_gamelog(player_id: int, season: str = "2024-25"):
    try:
        log = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        return log.get_normalized_dict()
    except:
        raise HTTPException(status_code=404, detail="Not found")

@app.get("/games/today")
def today_games():
    today = datetime.now().strftime("%Y-%m-%d")
    board = scoreboardv2.ScoreboardV2(game_date=today)
    return board.get_normalized_dict()

@app.get("/games/date/{date}")
def games_by_date(date: str):
    board = scoreboardv2.ScoreboardV2(game_date=date)
    return board.get_normalized_dict()

@app.get("/teams")
def all_teams():
    return teams.get_teams()