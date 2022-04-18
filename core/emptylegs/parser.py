from datetime import datetime
import json
import requests
import os
from time import strptime, mktime
from datetime import datetime

import aioredis
import asyncio
import aiohttp

class EmptyLegsParser:
    
    def __init__(self, session_id: int) -> None:
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': os.environ.get('API_TOKEN')
        }
        self.current_time = datetime.now().strftime('%Y-%m-%dT%H:%M')
        
        self.redis = aioredis.from_url(url='redis://redis_service', 
                                             port=6379, 
                                             db=session_id, 
                                             encoding='utf-8',
                                             decode_responses=True)

        self.airports_icao = set()
        self.airports_pos = dict()

    def get_availabilities(self) -> None:
        asyncio.run(self.get_availabilities_async())
    
    async def get_availabilities_async(self) -> None:
        
        # Page number count
        request_url = f'https://dir.aviapages.com/api/availabilities/?from_date_utc={self.current_time}'
        request = requests.get(url=request_url, headers=self.headers)
        if request.status_code == 200:
            request_json = request.json()
            if request_json.get('count') > 0:
                page_count = request_json.get('count') // request_json.get('per_page') + 1
                async with aiohttp.ClientSession(headers=self.headers, trust_env=True) as session:
                    tasks = []
                    for i in range(page_count):
                        tasks.append(asyncio.create_task(self.parse_availabilities_page(i, session)))
                    await asyncio.gather(*tasks)
    
    async def parse_availabilities_page(self, page_number: int, session) -> None:
        request_url = f'https://dir.aviapages.com/api/availabilities/?from_date_utc={self.current_time}&page={page_number}'
        async with session.get(request_url) as request:
            if request.status == 200:
                request_json = await request.json()
                if request_json.get('count') > 0:
                    for result in request_json.get('results'):
                        airport_from_pos = await self.get_airport_pos(result.get('dep_airport_icao'), session)
                        airport_to_pos = await self.get_airport_pos(result.get('arrival_airport_icao'), session)
                        if airport_from_pos is not None and airport_to_pos is not None:
                            date_from_struct = strptime(result.get('from_date_utc'), '%Y-%m-%dT%H:%M')
                            date_from = datetime.fromtimestamp(mktime(date_from_struct)).strftime('%d.%m')
                            date_to_struct = strptime(result.get('to_date_utc'), '%Y-%m-%dT%H:%M')
                            date_to = datetime.fromtimestamp(mktime(date_to_struct)).strftime('%d.%m')
                            dates = f'{date_from}-{date_to}'
                            value = json.dumps({
                                'registration_number': result.get('registration_number'),
                                'aircraft_type': result.get('aircraft_type'),
                                'company': result.get('company'),
                                'dep_airport_icao': result.get('dep_airport_icao'),
                                'arrival_airport_icao': result.get('arrival_airport_icao'),
                                'from_date_utc': result.get('from_date_utc'),
                                'to_date_utc': result.get('to_date_utc'),
                                'dates': dates,
                                'comment': result.get('comment'),
                                'location_from_lat': airport_from_pos.get('lat'),
                                'location_from_lon': airport_from_pos.get('lon'),
                                'location_to_lat': airport_to_pos.get('lat'),
                                'location_to_lon': airport_to_pos.get('lon'),
                                'price': result.get('price')
                            })
                            await self.redis.lpush(result.get('dep_airport_icao'), value)

    async def get_airport_pos(self, airport_icao: str, session) -> dict | None:
        if airport_icao in self.airports_icao:
            return self.airports_pos.get(airport_icao)
        else:
            self.airports_icao.add(airport_icao)
            request_url = f'https://dir.aviapages.com/api/airports/?search_icao={airport_icao}'
            async with session.get(request_url) as request:
                if request.status == 200:
                    request_json = await request.json()
                    if request_json.get('count') > 0:
                        result = request_json.get('results')[0]
                        airport_pos = {
                            'lat': result.get('latitude'),
                            'lon': result.get('longitude')
                        }
                        self.airports_pos.update({airport_icao: airport_pos})
                        return airport_pos
            
            return None
            
if __name__ == '__main__':
    print('Only for import!')
