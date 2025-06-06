import aiohttp

from app.config.settings import settings
        
async def fetch_member_info(team_id, user_id, cookies):
    url = f'{settings.BACKEND_BASE_URL}/teams/{team_id}/members?user_id={user_id}'
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, cookies=cookies) as response:
            if response.status == 200:
                return await response.json()
            return None
