from django.urls import path, include

from emptylegs.views import MarkersMapView

app_name = 'emptylegs'

urlpatterns = [
    path('__debug__/', include('debug_toolbar.urls')),
    path('', MarkersMapView.as_view()),
]
