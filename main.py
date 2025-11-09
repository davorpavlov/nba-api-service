from fastapi import FastAPI, HTTPException
from nba_api.stats.endpoints import scoreboardv2, playergamelog, commonplayerinfo
from nba_api.stats.static import players, teams
from datetime import datetime, timedelta
import time
import os
import requests

app = FastAPI(title="NBA API with Proxy")

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

# Proxy setup
PROXY_URL = os.getenv("PROXY_URL", None)
PROXIES = None

if PROXY_URL:
    # Format za requests library
    PROXIES = {
        'http': PROXY_URL,
        'https': PROXY_URL
    }

# Cache
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
        "proxy_format": "configured" if PROXIES else "not configured"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "proxy": "enabled" if PROXY_URL else "disabled",
        "cache_entries": len(cache_store)
    }

@app.get("/test-proxy")
def test_proxy():
    """Test da li proxy radi"""
    if not PROXY_URL:
        return {"error": "Proxy not configured"}
    
    try:
        response = requests.get(
            "https://httpbin.org/ip",
            proxies=PROXIES,
            timeout=10
        )
        return {
            "proxy_works": True,
            "your_ip": response.json(),
            "message": "Proxy is working!"
        }
    except Exception as e:
        return {
            "proxy_works": False,
            "error": str(e),
            "message": "Proxy connection failed"
        }

@app.get("/players/search")
def search_players(name: str):
    results = players.find_players_by_full_name(name)
    return results if results else []

@app.get("/teams")
def all_teams():
    return teams.get_teams()

@app.get("/games/today")
def today_games():
    cache_key = "games_today"
    cached = get_cache(cache_key, ttl_minutes=5)
    if cached:
        return {"cached": True, "data": cached}
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        time.sleep(0.6)
        
        # Pokušaj bez proxy parametra, nego postavimo SESSION sa proxy-jem
        import nba_api.stats.library.http as nba_http
        
        # Monkey patch session
        if PROXIES:
            original_send = nba_http.NBAStatsHTTP._send_api_request
            
            def patched_send(self, endpoint, parameters, referer=None, headers=None, timeout=None):
                session = requests.Session()
                session.proxies.update(PROXIES)
                # Sad koristi session sa proxy-jem
                url = f"https://stats.nba.com/stats/{endpoint}"
                response = session.get(
                    url, 
                    params=parameters,
                    headers=headers or NBA_HEADERS,
                    timeout=timeout or 100
                )
                return response
            
            nba_http.NBAStatsHTTP._send_api_request = patched_send
        
        board = scoreboardv2.ScoreboardV2(
            game_date=today,
            headers=NBA_HEADERS,
            timeout=100
        )
        data = board.get_normalized_dict()
        set_cache(cache_key, data)
        return {"cached": False, "data": data}
    except Exception as e:
        return {
            "error": str(e),
            "date": today,
            "message": "NBA API request failed",
            "tip": "Try /test-proxy to check if proxy is working"
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
            proxy=PROXY_URL,
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