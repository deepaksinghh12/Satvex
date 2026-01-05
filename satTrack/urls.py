from django.urls import path 
from django.views.generic import TemplateView
from .views import (
    data, data_buffer, list_view, search_page, search_word, sensor_list, 
    detail_view, compare_tle, about_page, fetch_latest, pass_predictor, 
    calculate_passes_view, multi_satellite_viewer, satellite_imagery_view,
    get_satellite_dem, get_satellite_imagery, get_location_imagery, bhuvan_capabilities,
    wms_proxy, download_satellite_imagery, satellite_comparison_view,
    get_satellites_list, compare_satellites, tle_comparison_view, get_tle_comparison
)

urlpatterns = [
    path('', search_page, name="search_page"),
    path('searchword', search_word, name='search_word'),
    path('sat', list_view.as_view(), name='list_view'),
    path('about', about_page, name="about_page"),
    path('pass-predictor', pass_predictor, name='pass_predictor'),
    path('calculate-passes', calculate_passes_view, name='calculate_passes'),
    path('multi-viewer', multi_satellite_viewer, name='multi_satellite_viewer'),
    path('comparison', satellite_comparison_view, name='satellite_comparison'),
    path('tle-comparison', tle_comparison_view, name='tle_comparison'),
    path('test-bhuvan', TemplateView.as_view(template_name='test_bhuvan.html'), name='test_bhuvan'),
    
    # Satellite imagery and DEM data endpoints (must come before generic sat/<id>/<sensor>)
    path('sat/<int:norad_id>/imagery', satellite_imagery_view, name='satellite_imagery'),
    path('sat/<int:norad_id>/compare', compare_tle, name='compare'),
    path('sat/<int:norad_id>/save', fetch_latest, name='fetch'),
    
    # API endpoints
    path('api/sat/<int:norad_id>/dem', get_satellite_dem, name='get_satellite_dem'),
    path('api/sat/<int:norad_id>/imagery', get_satellite_imagery, name='get_satellite_imagery'),
    path('api/sat/<int:norad_id>/download', download_satellite_imagery, name='download_satellite_imagery'),
    path('api/location/imagery', get_location_imagery, name='get_location_imagery'),
    path('api/bhuvan/capabilities', bhuvan_capabilities, name='bhuvan_capabilities'),
    path('api/satellites/list', get_satellites_list, name='get_satellites_list'),
    path('api/satellites/compare', compare_satellites, name='compare_satellites'),
    path('api/satellites/<int:norad_id>/tle-comparison', get_tle_comparison, name='get_tle_comparison'),
    path('proxy/wms', wms_proxy, name='proxy_wms'),
    
    # Data endpoints
    path('data/<int:norad_id>', data, name='data'),
    path('databuffer/<int:norad_id>', data_buffer, name='databuffer'),
    
    # Generic satellite routes (must come last to avoid conflicts)
    path('sat/<int:norad_id>', sensor_list, name="detail_view"),
    path('sat/<int:norad_id>/<str:sensor_name>', detail_view, name='detail_view_sensor'),
]

