from fastapi import FastAPI, HTTPException
from nba_api.stats.endpoints import scoreboardv2, playergamelog, commonplayerinfo
from nba_api.stats.static import players, teams
from datetime import datetime
import time

app = FastAPI(title="NBA API")

# Custom headers za NBA API (kopirano iz dokumentacije)
NBA_HEADERS = {
    'Host': 'stats.nba.com',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

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
        time.sleep(0.6)
        # Headers kao parametar!
        info = commonplayerinfo.CommonPlayerInfo(
            player_id=player_id, 
            headers=NBA_HEADERS, 
            timeout=100
        )
        return info.get_normalized_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/gamelog")
def player_gamelog(player_id: int, season: str = "2024-25"):
    try:
        time.sleep(0.6)
        # Headers kao parametar!
        log = playergamelog.PlayerGameLog(
            player_id=player_id, 
            season=season,
            headers=NBA_HEADERS,
            timeout=100
        )
        return log.get_normalized_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/games/today")
def today_games():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        time.sleep(0.6)
        # Headers kao parametar!
        board = scoreboardv2.ScoreboardV2(
            game_date=today,
            headers=NBA_HEADERS,
            timeout=100
        )
        return board.get_normalized_dict()
    except Exception as e:
        return {
            "error": str(e),
            "date": today,
            "message": "NBA API request failed"
        }

@app.get("/games/date/{date}")
def games_by_date(date: str):
    try:
        time.sleep(0.6)
        # Headers kao parametar!
        board = scoreboardv2.ScoreboardV2(
            game_date=date,
            headers=NBA_HEADERS,
            timeout=100
        )
        return board.get_normalized_dict()
    except Exception as e:
        return {
            "error": str(e),
            "date": date,
            "message": "NBA API request failed"
        }

@app.get("/teams")
def all_teams():
    return teams.get_teams()