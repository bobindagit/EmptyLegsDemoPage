from django.views.generic import View
from django.shortcuts import render

from .parser import EmptyLegsParser
from .tables import EmptyLegsTable
from .forms import EmptyLegsFilters

from time import strptime, mktime
from datetime import datetime
import json

from redis import Redis

from core.settings import MAPBOX_TOKEN


class MarkersMapView(View):
    template_name = 'map.html'

    def get(self, request, *args, **kwargs):
        request_data = self.get_request_data()
        return render(request, self.template_name, request_data)
        
    def post(self, request, *args, **kwargs):
        request_data = self.get_request_data()
        return render(request, self.template_name, request_data)

    def get_request_data(self) -> dict:
        
        session_id = self.request.session.session_key
        
        # Updating empty legs data in redis
        if self.request.method == 'GET':
            parser = EmptyLegsParser(session_id)
            parser.get_availabilities()
        
        # Markers
        features = []
        
        # Empty legs table
        availabilities = []
        
        # Form
        form = EmptyLegsFilters(self.request.POST)
        
        # Filters from the form
        if self.request.method == 'POST':
            filter_date = form['filter_date'].value()
            if filter_date:
                date_struct = strptime(filter_date, '%Y-%m-%dT%H:%M')
                filter_date = datetime.fromtimestamp(mktime(date_struct))
            filter_company = form['filter_company'].value()
            filter_departure_airport = form['filter_departure_airport'].value()
            filter_arrival_airport = form['filter_arrival_airport'].value()
            filter_aircraft = form['filter_aircraft'].value()
            filters_installed = filter_date or filter_company or filter_departure_airport or filter_arrival_airport or filter_aircraft
        else:
            filters_installed = False
        
        # Generating markers data
        redis = Redis.from_url(url='redis://redis_service', port=6379, db=session_id, encoding='utf-8', decode_responses=True)
        for redis_key in redis.scan_iter():
            marker_name = ''
            location_lon = 0
            location_lat = 0
            arrivals = []
            for availability in redis.lrange(redis_key, 0, redis.llen(redis_key)):
                value = json.loads(availability)
                
                # Filters check
                if not filters_installed or self.filters_check_passed(filter_date,
                                                                      filter_company,
                                                                      filter_departure_airport,
                                                                      filter_arrival_airport,
                                                                      filter_aircraft,
                                                                      value):
                    availabilities.append(value)
                    
                    location_lon = value.get('location_from_lon')
                    location_lat = value.get('location_from_lat')
                    
                    date_struct = strptime(value.get('from_date_utc'), '%Y-%m-%dT%H:%M')
                    dt = datetime.fromtimestamp(mktime(date_struct))
                    
                    # Markers name
                    new_marker = f'{dt.strftime("%d%b")} {value.get("company")} {value.get("aircraft_type")} {value.get("arrival_airport_icao")} <br>'
                    if new_marker not in marker_name:
                        marker_name += new_marker
                        
                    # Arrival airport
                    if value.get('location_to_lat') and value.get('location_to_lon'):
                        arrivals.append([[location_lat, location_lon], [value.get('location_to_lat'), value.get('location_to_lon')]])

            if marker_name:
                features.append(self.serialize_marker(marker_name.strip(), location_lon, location_lat, arrivals))
        
        emptylegs_table = EmptyLegsTable(availabilities)
        
        # Serializing all markers
        markers = self.serialize_markers(features)
        
        return {
            'emptylegs_table': emptylegs_table,
            'form': form,
            'markers': markers,
            'MAPBOX_TOKEN': {'token': MAPBOX_TOKEN}
        }

    @staticmethod
    def filters_check_passed(date: str, company: str, departure: str, arrival: str, aircraft: str, value: dict) -> bool:
        if date:
            # Converting to datetime format
            value_struct = strptime(value.get('from_date_utc'), '%Y-%m-%dT%H:%M')
            value_date = datetime.fromtimestamp(mktime(value_struct))
            if date > value_date:
                return False
        if company and company.upper() != value.get('company').upper():
            return False
        if departure and departure.upper() != value.get('dep_airport_icao').upper():
            return False
        if arrival and arrival.upper() != value.get('arrival_airport_icao').upper():
            return False
        if aircraft and aircraft.upper() != value.get('aircraft_type').upper():
            return False
        
        return True
    
    @staticmethod
    def serialize_marker(name: str, location_lon: float, location_lat: float, arrivals: list) -> dict:
        return {
            "type": "Feature",
            "properties": {"name": name, 'arrivals': arrivals},
            "geometry": {
                "type": "Point",
                "coordinates": list([location_lon, location_lat])
            }
        }
    
    @staticmethod
    def serialize_markers(features: list) -> dict:
        return {
            "type": "FeatureCollection",
            "features": features
        }
    