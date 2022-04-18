import django_tables2 as tables


class EmptyLegsTable(tables.Table):
    aircraft_type = tables.Column(verbose_name="Aircraft")
    company = tables.Column(verbose_name="Company")
    dep_airport_icao = tables.Column(verbose_name="Departure")
    arrival_airport_icao = tables.Column(verbose_name="Arrival")
    dates = tables.Column(verbose_name="Dates")
    price = tables.Column(verbose_name="Price")
    comment = tables.Column(verbose_name="Comment")
