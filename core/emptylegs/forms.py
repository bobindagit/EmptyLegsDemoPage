from django import forms
from .widget import DateTimePickerInput


class EmptyLegsFilters(forms.Form):
    filter_date = forms.DateTimeField(label='Date from', required=False, input_formats=['%Y-%m-%dT%H:%M'], widget=DateTimePickerInput())
    filter_company = forms.CharField(label='Company', required=False)
    filter_departure_airport = forms.CharField(label='Departure (ICAO)', required=False, max_length=4)
    filter_arrival_airport = forms.CharField(label='Arrival (ICAO)', required=False, max_length=4)
    filter_aircraft = forms.CharField(label='Aircraft', required=False)
    