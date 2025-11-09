from fastapi import FastAPI, HTTPException
from nba_api.stats.endpoints import scoreboardv2, playergamelog, commonplayerinfo
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
import time
import os

app = FastAPI(title="NBA API with Proxy")

# Custom headers
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

# Proxy config - čita iz environment variables
PROXY_URL = os.getenv("PROXY_URL", None)  # Format: http://username:password@proxy.com:port

# Simple cache
cache_store = {}

def get_cache(key: str, ttl_minutes: int = 5):
    if key in cache_store:
        data, timestamp = cache_store[key]
        if datetime.now() - timestamp < timedelta(minutes=ttl_minutes):
            return data
    return None

def set_cache(key: str, data):
    cache_store[key] = (data, datetime.now())

@app.get("/")
def root():
    return {
        "status": "online", 
        "service": "NBA API",
        "proxy_enabled": PROXY_URL is not None,
        "cache_enabled": True,
        "endpoints": {
            "health": "/health",
            "teams": "/teams",
            "search": "/players/search?name=LeBron",
            "player_info": "/player/{id}/info",
            "player_gamelog": "/player/{id}/gamelog?season=2024-25",
            "today": "/games/today",
            "by_date": "/games/date/2024-11-08"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "proxy": "enabled" if PROXY_URL else "disabled",
        "cache_entries": len(cache_store)
    }

@app.get("/players/search")
def search_players(name: str):
    results = players.find_players_by_full_name(name)
    return results if results else []

@app.get("/player/{player_id}/info")
def player_info(player_id: int):
    cache_key = f"player_info_{player_id}"
    cached = get_cache(cache_key, ttl_minutes=60)
    if cached:
        return {"cached": True, "data": cached}
    
    try:
        time.sleep(0.6)
        info = commonplayerinfo.CommonPlayerInfo(
            player_id=player_id, 
            headers=NBA_HEADERS,
            proxy=PROXY_URL,  # DODAJ PROXY!
            timeout=100
        )
        data = info.get_normalized_dict()
        set_cache(cache_key, data)
        return {"cached": False, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/gamelog")
def player_gamelog(player_id: int, season: str = "2024-25"):
    cache_key = f"gamelog_{player_id}_{season}"
    cached = get_cache(cache_key, ttl_minutes=60)
    if cached:
        return {"cached": True, "data": cached}
    
    try:
        time.sleep(0.6)
        log = playergamelog.PlayerGameLog(
            player_id=player_id, 
            season=season,
            headers=NBA_HEADERS,
            proxy=PROXY_URL,  # DODAJ PROXY!
            timeout=100
        )
        data = log.get_normalized_dict()
        set_cache(cache_key, data)
        return {"cached": False, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/games/today")
def today_games():
    cache_key = "games_today"
    cached = get_cache(cache_key, ttl_minutes=5)
    if cached:
        return {"cached": True, "data": cached}
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        time.sleep(0.6)
        
        board = scoreboardv2.ScoreboardV2(
            game_date=today,
            headers=NBA_HEADERS,
            proxy=PROXY_URL,  # DODAJ PROXY!
            timeout=100
        )
        data = board.get_normalized_dict()
        set_cache(cache_key, data)
        return {"cached": False, "data": data}
    except Exception as e:
        return {
            "error": str(e),
            "date": today,
            "message": "NBA API request failed"
        }

@app.get("/games/date/{date}")
def games_by_date(date: str):
    cache_key = f"games_{date}"
    cached = get_cache(cache_key, ttl_minutes=10)
    if cached:
        return {"cached": True, "data": cached}
    
    try:
        time.sleep(0.6)
        board = scoreboardv2.ScoreboardV2(
            game_date=date,
            headers=NBA_HEADERS,
            proxy=PROXY_URL,  # DODAJ PROXY!
            timeout=100
        )
        data = board.get_normalized_dict()
        set_cache(cache_key, data)
        return {"cached": False, "data": data}
    except Exception as e:
        return {
            "error": str(e),
            "date": date,
            "message": "NBA API request failed"
        }

@app.get("/teams")
def all_teams():
    return teams.get_teams()

@app.get("/cache/clear")
def clear_cache():
    cache_store.clear()
    return {"message": "Cache cleared"}