from fastapi import FastAPI, HTTPException
from nba_api.stats.endpoints import scoreboardv2, playergamelog, commonplayerinfo
from nba_api.stats.static import players, teams
from datetime import datetime
import time

# KLJUČNO: Konfiguriši NBA API da koristi browser headers
from nba_api.stats.library.http import NBAStatsHTTP

# Postavi custom headers da izgledamo kao pravi browser
NBAStatsHTTP.timeout = 60
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'Connection': 'keep-alive',
}
NBAStatsHTTP.send_api_request = lambda self, endpoint, parameters: self._send_api_request(
    endpoint=endpoint, 
    parameters=parameters, 
    headers=headers
)

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
        time.sleep(0.6)  # Rate limiting
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        return info.get_normalized_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/gamelog")
def player_gamelog(player_id: int, season: str = "2024-25"):
    try:
        time.sleep(0.6)
        log = playergamelog.PlayerGameLog(player_id=player_id, season=season)
        return log.get_normalized_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/games/today")
def today_games():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        time.sleep(0.6)
        board = scoreboardv2.ScoreboardV2(game_date=today)
        return board.get_normalized_dict()
    except Exception as e:
        return {
            "error": str(e),
            "date": today,
            "tip": "NBA API može biti spor ili blokirati requestove. Pokušaj ponovo za 30 sekundi."
        }

@app.get("/games/date/{date}")
def games_by_date(date: str):
    try:
        time.sleep(0.6)
        board = scoreboardv2.ScoreboardV2(game_date=date)
        return board.get_normalized_dict()
    except Exception as e:
        return {
            "error": str(e),
            "date": date,
            "tip": "NBA API može biti spor ili blokirati requestove. Pokušaj ponovo za 30 sekundi."
        }

@app.get("/teams")
def all_teams():
    return teams.get_teams()