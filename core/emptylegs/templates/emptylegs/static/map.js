var map = L.map('map', {scrollWheelZoom: false}).setView([0,0], 2);
var mapbox_token = JSON.parse(document.getElementById('MAPBOX_TOKEN').textContent)['token'];
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=' + mapbox_token, {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
    maxZoom: 18,
    id: 'mapbox/streets-v11',
    tileSize: 512,
    zoomOffset: -1,
    accessToken: mapbox_token
}).addTo(map);

map.on('focus', function() { map.scrollWheelZoom.enable(); });
map.on('blur', function() { map.scrollWheelZoom.disable(); });

// Markers
var data = JSON.parse(document.getElementById('markers').textContent);
L.geoJSON(data, {
    pointToLayer: function(feature, latlng) {
        return L.marker(latlng, {
            icon: new L.DivIcon({
                className: 'divIcon',
                html: '<div id="iconHeader" style="background-color: #333; white-space: pre-wrap; color: rgb(255, 255, 255); line-height: 110%; font-size: 9px; font-weight: bold; width: 35px; height: 15px; text-align: center; padding: 3px;">' + feature.properties.header + '</div>'
            })
        })
    }
}).bindPopup(function (layer) { return layer.feature.properties.name; }).addTo(map).on('click', markerOnClick);

var polylines = [];

function markerOnClick(event) {
    clearPolylines()
    var clickedMarker = event.layer;
    var arrivals = clickedMarker.feature.properties.arrivals
    var polyline = L.polyline(arrivals, {color: 'red', weight: 2}).addTo(map); // route lines
    polylines.push(polyline)
};

function clearPolylines() {
    polylines.forEach(function (item) {
        map.removeLayer(item)
    });
}
