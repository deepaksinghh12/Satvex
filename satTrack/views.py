from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from sgp4.api import Satrec 
from sgp4.api import jday 
import pandas as pd 
from .extract_data import convert, get_live_data, data_over_time, get_position
from django.utils import timezone
from django.views.generic.list import ListView
from django.urls import reverse
from .models import Satellite, Sensor, TLE
from datetime import datetime, timedelta
import requests
from .satellite_data_api import SatelliteDataManager, BhuvanAPI
import urllib.parse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, FileResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache

def about_page(request):
    return render(request, 'about.html')

def search_page(request):
    model = Satellite
    # all_objects = Satellite.objects.all()
    # for object in all_objects:
    #     object.save()
    return render(request, 'search.html')


def search_word(request):
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        word = request.GET.get('word', None)
        sat_list = []
        id_dict = {}
        if word:
            sat_objs = Satellite.objects.filter(name__icontains=word)
            for sat in sat_objs:
                id_dict[sat.name] = sat.norad_id
                # print(id_dict)
                sat_list.append(sat.name)
        return JsonResponse({'sat_list': sat_list, 'id_dict': id_dict}, status=200)
    else: 
        return 

    


def data(request, norad_id):
    satellite = Satellite.objects.get(pk=norad_id)
    TLE_DATA = satellite.tle_now
    save_dict = convert(TLE_DATA)


  

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        lat = request.GET.get("cur_loc_lat", None)
        lon = request.GET.get("cur_loc_lon", None)
        compare_tle = request.GET.get("compare_tle", None)
        position = get_live_data(TLE_DATA, {'lat':lat, 'lon':lon})
        if compare_tle:
            TLE_COMPARE = TLE.objects.get(id=compare_tle).tle
            position1 = get_live_data(TLE_COMPARE, {'lat':lat, 'lon':lon})
        else:
            position1 = position
            
        diff = {'lat': position['lat'] - position1['lat'], 
                'lon': position['lon'] - position1['lon'], 
                'height': position['height'] - position1['height'], 
                }
        
        if request.method == 'GET':
            return JsonResponse({'context': position1,'difference':diff})
        return JsonResponse({'status': 'Invalid request'}, status=400)
        
    else:
        context = {'data': save_dict}
        return render(request, 'data.html', context)


def data_buffer(request, norad_id):
    satellite = Satellite.objects.get(pk=norad_id)
    TLE_DATA = satellite.tle_now
    period = convert(TLE_DATA)['period']

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        
        time_scale_pos = data_over_time(TLE_DATA, period)
    
        if request.method == 'GET':
            return JsonResponse({'context': time_scale_pos})

        return JsonResponse({'status': 'Invalid request'}, status=400)
    else: 
        return 


class list_view(ListView):
    model = Satellite
    paginate_by = 100  # if pagination is desired

    context_object_name = 'satellite_list'
    template_name = 'satellite_list.html'

def detail_view(request, norad_id, sensor_name):
    sensor = Sensor.objects.get(name=sensor_name)
    satellite = Satellite.objects.get(pk=norad_id)
    tle_list = satellite.tle_set.all()
    TLE_DATA = satellite.tle_now
    sat_data = convert(TLE_DATA)
    context =  {'satellite': satellite, 'data': sat_data, 'sensor': sensor, 'tle_list': tle_list}
    return render(request, 'home.html', context)

def sensor_list(request, norad_id):
    satellite = Satellite.objects.get(pk=norad_id)
    sensors = satellite.sensors.all()
    TLE_DATA = satellite.tle_now
    save_dict = convert(TLE_DATA)

    context = { 'satellite': satellite ,'sensors': sensors, 'data': save_dict}
    return render(request, 'sensors.html', context)


def fetch_latest(request, norad_id):
    satellite = Satellite.objects.get(pk=norad_id)
    satellite.save()
    return redirect(reverse('detail_view', kwargs={'norad_id':norad_id}))


def compare_tle(request, norad_id):
    print("running")
    satellite = Satellite.objects.get(pk=norad_id)
    tle_list = satellite.tle_set.all()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        id_1 = request.GET.get("tle1", None)
        id_2 = request.GET.get("tle2", None)
        time = request.GET.get("time", None)
        print(time)
        TLE1 = TLE.objects.get(id=id_1).tle
        TLE2 = TLE.objects.get(id=id_2).tle
        position = get_position(TLE1, time)
        position1 = get_position(TLE2, time)
        diff = {'lat': position['lat'] - position1['lat'], 
                'lon': position['lon'] - position1['lon'], 
                'height': position['height'] - position1['height'], 
                }
        if request.method == 'GET':
            return JsonResponse({'context': diff})
    else:
        context = {'satellite': satellite, 'tle_list': tle_list }
        return render(request, 'compare.html', context)


def pass_predictor(request):
    """View for satellite pass prediction"""
    return render(request, 'pass_predictor.html')


def multi_satellite_viewer(request):
    """View for displaying multiple satellites simultaneously"""
    satellites = Satellite.objects.all().order_by('name')
    context = {'satellites': satellites}
    return render(request, 'multi_satellite.html', context)


def get_location_coordinates(location_name):
    """Get coordinates from location name using Nominatim API"""
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {
            'q': location_name,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'SatTrack-Application'
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if data and len(data) > 0:
            return {
                'lat': float(data[0]['lat']),
                'lon': float(data[0]['lon']),
                'display_name': data[0]['display_name']
            }
    except Exception as e:
        print(f"Error getting coordinates: {e}")
    
    return None


def calculate_passes_view(request):
    """AJAX endpoint to calculate satellite passes"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_ajax:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    location_name = request.GET.get('location', None)
    hours_ahead = int(request.GET.get('hours', 48))
    min_elevation = float(request.GET.get('min_elevation', 10))
    
    if not location_name:
        return JsonResponse({'error': 'Location is required'}, status=400)
    
    # Get coordinates from location name
    location_data = get_location_coordinates(location_name)
    
    if not location_data:
        return JsonResponse({'error': 'Location not found. Please try a different search term.'}, status=404)
    
    observer_lat = location_data['lat']
    observer_lon = location_data['lon']
    observer_alt = 0  # Default altitude in meters
    
    # Get all satellites
    satellites = Satellite.objects.all()

    # Quick mitigation: limit number of satellites processed per request
    try:
        max_satellites = int(request.GET.get('max_satellites', 50))
    except Exception:
        max_satellites = 50

    # Cache results per (location,hours,min_elevation,max_satellites) to avoid
    # recalculating on repeated requests. Short TTL keeps data reasonably fresh.
    cache_key = f"passes:{location_name}:{hours_ahead}:{min_elevation}:{max_satellites}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)
    
    results = {
        'location': location_data['display_name'],
        'coordinates': {
            'lat': observer_lat,
            'lon': observer_lon
        },
        'satellites': []
    }
    
    # Import skyfield lazily to avoid network/cert operations at module import
    from skyfield.api import load, wgs84, EarthSatellite

    ts = load.timescale()
    observer = wgs84.latlon(observer_lat, observer_lon, observer_alt)
    t0 = ts.now()
    t1 = ts.utc(t0.utc_datetime() + timedelta(hours=hours_ahead))
    
    # Slice the queryset to only process up to `max_satellites` items.
    for satellite in satellites[:max_satellites]:
        if not satellite.tle_now:
            continue
        
        try:
            tle_lines = satellite.tle_now.strip().split('\n')
            if len(tle_lines) < 2:
                continue
            
            line1 = tle_lines[0].strip()
            line2 = tle_lines[1].strip()
            
            sat = EarthSatellite(line1, line2, satellite.name, ts)
            t, events = sat.find_events(observer, t0, t1, altitude_degrees=min_elevation)
            
            passes = []
            i = 0
            while i < len(events):
                if events[i] == 0:  # Rise event
                    rise_time = t[i]
                    max_time = None
                    max_elevation = 0
                    set_time = None
                    
                    j = i + 1
                    while j < len(events):
                        if events[j] == 1:  # Culmination
                            max_time = t[j]
                            difference = sat.at(max_time) - observer.at(max_time)
                            alt, az, distance = difference.altaz()
                            max_elevation = alt.degrees
                        elif events[j] == 2:  # Set
                            set_time = t[j]
                            break
                        j += 1
                    
                    if set_time is not None and max_time is not None:
                        rise_dt = rise_time.utc_datetime()
                        max_dt = max_time.utc_datetime()
                        set_dt = set_time.utc_datetime()
                        duration = (set_dt - rise_dt).total_seconds() / 60
                        
                        # Calculate rise/set azimuth
                        rise_diff = sat.at(rise_time) - observer.at(rise_time)
                        rise_alt, rise_az, _ = rise_diff.altaz()
                        
                        set_diff = sat.at(set_time) - observer.at(set_time)
                        set_alt, set_az, _ = set_diff.altaz()
                        
                        # Convert to IST
                        ist_rise = rise_dt + timedelta(hours=5, minutes=30)
                        ist_max = max_dt + timedelta(hours=5, minutes=30)
                        ist_set = set_dt + timedelta(hours=5, minutes=30)
                        
                        passes.append({
                            'rise_utc': rise_dt.strftime('%Y-%m-%d %H:%M:%S'),
                            'rise_ist': ist_rise.strftime('%Y-%m-%d %H:%M:%S'),
                            'rise_azimuth': round(rise_az.degrees, 1),
                            'max_utc': max_dt.strftime('%Y-%m-%d %H:%M:%S'),
                            'max_ist': ist_max.strftime('%Y-%m-%d %H:%M:%S'),
                            'max_elevation': round(max_elevation, 1),
                            'set_utc': set_dt.strftime('%Y-%m-%d %H:%M:%S'),
                            'set_ist': ist_set.strftime('%Y-%m-%d %H:%M:%S'),
                            'set_azimuth': round(set_az.degrees, 1),
                            'duration': round(duration, 1)
                        })
                    
                    i = j
                i += 1
            
            if passes:
                results['satellites'].append({
                    'name': satellite.name,
                    'norad_id': satellite.norad_id,
                    'passes': passes
                })

        except Exception as e:
            print(f"Error calculating passes for {satellite.name}: {e}")
            continue
    # Cache for 10 minutes
    try:
        cache.set(cache_key, results, timeout=60 * 10)
    except Exception:
        pass

    return JsonResponse(results)


def satellite_imagery_view(request, norad_id):
    """View to display satellite imagery and DEM data"""
    satellite = Satellite.objects.get(pk=norad_id)
    context = {
        'satellite': satellite,
        'available_layers': BhuvanAPI.LAYERS
    }
    return render(request, 'satellite_imagery.html', context)


def get_satellite_dem(request, norad_id):
    """AJAX endpoint to fetch DEM data for satellite's current position"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_ajax:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        satellite = Satellite.objects.get(pk=norad_id)
        TLE_DATA = satellite.tle_now
        
        if not TLE_DATA:
            return JsonResponse({'error': 'TLE data not available'}, status=404)
        
        # Calculate current satellite position
        tle_lines = TLE_DATA.strip().split('\n')
        if len(tle_lines) < 2:
            return JsonResponse({'error': 'Invalid TLE data'}, status=400)
        
        # Lazy import skyfield here
        from skyfield.api import load, EarthSatellite

        ts = load.timescale()
        sat = EarthSatellite(tle_lines[0], tle_lines[1], satellite.name, ts)
        t = ts.now()
        geocentric = sat.at(t)
        subpoint = geocentric.subpoint()
        
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        height = subpoint.elevation.km
        
        # Get DEM data for the location
        data_manager = SatelliteDataManager()
        radius_km = float(request.GET.get('radius', 50))
        
        dem_data = data_manager.get_imagery_for_satellite_position(
            lat, lon, radius_km, data_type='dem'
        )
        
        if dem_data and dem_data.get('success'):
            response_data = {
                'success': True,
                'satellite_position': {
                    'lat': round(lat, 4),
                    'lon': round(lon, 4),
                    'height_km': round(height, 2)
                },
                'dem_data': dem_data,
                'timestamp': datetime.now().isoformat()
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Could not fetch DEM data',
                'satellite_position': {
                    'lat': round(lat, 4),
                    'lon': round(lon, 4),
                    'height_km': round(height, 2)
                }
            })
    
    except Satellite.DoesNotExist:
        return JsonResponse({'error': 'Satellite not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_satellite_imagery(request, norad_id):
    """AJAX endpoint to fetch optical imagery for satellite's current position"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_ajax:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        satellite = Satellite.objects.get(pk=norad_id)
        TLE_DATA = satellite.tle_now
        
        if not TLE_DATA:
            return JsonResponse({'error': 'TLE data not available'}, status=404)
        
        # Calculate current satellite position
        tle_lines = TLE_DATA.strip().split('\n')
        if len(tle_lines) < 2:
            return JsonResponse({'error': 'Invalid TLE data'}, status=400)
        
        ts = load.timescale()
        sat = EarthSatellite(tle_lines[0], tle_lines[1], satellite.name, ts)
        t = ts.now()
        geocentric = sat.at(t)
        subpoint = geocentric.subpoint()
        
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        height = subpoint.elevation.km
        
        # Check if satellite is over India region (Bhuvan coverage)
        # India bounding box approximately: lat 6-37, lon 68-97
        is_over_india = (6 <= lat <= 37) and (68 <= lon <= 97)
        
        if not is_over_india:
            return JsonResponse({
                'success': False,
                'error': 'Satellite is not over India region',
                'message': 'Bhuvan only provides imagery for India. Satellite is currently over a different region.',
                'satellite_position': {
                    'lat': round(lat, 4),
                    'lon': round(lon, 4),
                    'height_km': round(height, 2)
                },
                'coverage_info': 'Try again when satellite passes over India (lat: 6-37°, lon: 68-97°)'
            })
        
        # Get optical imagery for the location
        data_manager = SatelliteDataManager()
        radius_km = float(request.GET.get('radius', 50))
        
        imagery_data = data_manager.get_imagery_for_satellite_position(
            lat, lon, radius_km, data_type='optical'
        )
        
        if imagery_data and imagery_data.get('success'):
            response_data = {
                'success': True,
                'satellite_position': {
                    'lat': round(lat, 4),
                    'lon': round(lon, 4),
                    'height_km': round(height, 2)
                },
                'imagery_data': imagery_data,
                'timestamp': datetime.now().isoformat()
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'error': 'Could not fetch imagery data',
                'satellite_position': {
                    'lat': round(lat, 4),
                    'lon': round(lon, 4),
                    'height_km': round(height, 2)
                }
            })
    
    except Satellite.DoesNotExist:
        return JsonResponse({'error': 'Satellite not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_location_imagery(request):
    """AJAX endpoint to fetch imagery for any location"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if not is_ajax:
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        lat = float(request.GET.get('lat'))
        lon = float(request.GET.get('lon'))
        radius_km = float(request.GET.get('radius', 50))
        data_type = request.GET.get('type', 'optical')
        layer = request.GET.get('layer', 'india3')  # Use india3 - proven working
        
        data_manager = SatelliteDataManager()
        
        if data_type == 'dem':
            result = data_manager.get_imagery_for_satellite_position(
                lat, lon, radius_km, data_type='dem'
            )
        else:
            # For custom layer selection
            radius_deg = radius_km / 111.0
            bbox = (
                lon - radius_deg,
                lat - radius_deg,
                lon + radius_deg,
                lat + radius_deg
            )
            result = data_manager.bhuvan.get_ortho_image(bbox, satellite=layer)
        
        if result and result.get('success'):
            return JsonResponse({
                'success': True,
                'location': {'lat': lat, 'lon': lon},
                'data': result,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Could not fetch data',
                'location': {'lat': lat, 'lon': lon}
            })
    
    except (ValueError, TypeError) as e:
        return JsonResponse({'error': f'Invalid parameters: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def bhuvan_capabilities(request):
    """Get available Bhuvan WMS layers"""
    bhuvan = BhuvanAPI()
    capabilities = bhuvan.get_capabilities()
    
    return JsonResponse({
        'layers': BhuvanAPI.LAYERS,
        'capabilities': capabilities
    })


@require_GET
def download_satellite_imagery(request, norad_id):
    """Download high-resolution imagery for satellite's current position as file.
    
    Query params:
    - radius: radius in km (default 50)
    - layer: layer name (default resourcesat2)
    - format: png or tiff (default png)
    """
    try:
        satellite = Satellite.objects.get(pk=norad_id)
        TLE_DATA = satellite.tle_now
        
        if not TLE_DATA:
            return JsonResponse({'error': 'TLE data not available'}, status=404)
        
        # Calculate position
        tle_lines = TLE_DATA.strip().split('\n')
        if len(tle_lines) < 2:
            return JsonResponse({'error': 'Invalid TLE data'}, status=400)
        
        ts = load.timescale()
        sat = EarthSatellite(tle_lines[0], tle_lines[1], satellite.name, ts)
        t = ts.now()
        geocentric = sat.at(t)
        subpoint = geocentric.subpoint()
        
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        
        # Check if satellite is over India region (Bhuvan coverage)
        is_over_india = (6 <= lat <= 37) and (68 <= lon <= 97)
        
        if not is_over_india:
            return JsonResponse({
                'error': 'Satellite not over India',
                'message': f'Satellite is at ({lat:.2f}°, {lon:.2f}°) which is outside Bhuvan coverage area (India: Lat 6-37°, Lon 68-97°)',
                'suggestion': 'Please wait for satellite to pass over India, or use manual location with Indian coordinates'
            }, status=400)
        
        # Get parameters
        radius_km = float(request.GET.get('radius', 50))
        layer = request.GET.get('layer', 'india3')  # Use working layer
        img_format = request.GET.get('format', 'png')
        
        # Fetch high-res imagery (no validation needed, we know india3 works)
        data_manager = SatelliteDataManager()
        radius_deg = radius_km / 111.0
        bbox = (lon - radius_deg, lat - radius_deg, lon + radius_deg, lat + radius_deg)
        
        image_data = data_manager.bhuvan.get_satellite_imagery(
            bbox=bbox,
            layer=layer,
            width=2048,
            height=2048,
            format=f'image/{img_format}'
        )
        
        if not image_data:
            return JsonResponse({
                'error': 'Could not fetch imagery',
                'details': 'Bhuvan WMS returned no data. The layer may not have coverage for this specific location.'
            }, status=500)
        
        # Return as file download
        response = HttpResponse(image_data, content_type=f'image/{img_format}')
        filename = f"{satellite.name.replace(' ', '_')}_{layer}_{lat:.2f}_{lon:.2f}.{img_format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Satellite.DoesNotExist:
        return JsonResponse({'error': 'Satellite not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
@csrf_exempt
@cache_page(60 * 15)  # Cache tiles for 15 minutes
def wms_proxy(request):
    """Proxy WMS requests to Bhuvan to avoid CORS and allow caching/auth.

    This view validates parameters and forwards to Bhuvan WMS.
    Cached for 15 minutes to reduce upstream load.
    """
    try:
        # Validate allowed layers (security: prevent arbitrary layer requests)
        allowed_layers = list(BhuvanAPI.LAYERS.keys())
        layer = request.GET.get('LAYERS', '')
        
        if layer and layer not in allowed_layers:
            return JsonResponse({'error': f'Layer {layer} not allowed'}, status=400)
        
        # Validate image dimensions (prevent abuse)
        try:
            width = int(request.GET.get('WIDTH', 256))
            height = int(request.GET.get('HEIGHT', 256))
            if width > 2048 or height > 2048 or width < 1 or height < 1:
                return JsonResponse({'error': 'Invalid dimensions (1-2048)'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Invalid width/height'}, status=400)
        
        # Upstream Bhuvan WMS endpoint (only this host allowed)
        upstream = BhuvanAPI.WMS_BASE_URL

        # Build upstream URL with original query string
        qs = request.META.get('QUERY_STRING', '')
        url = f"{upstream}?{qs}" if qs else upstream

        # Forward request
        resp = requests.get(url, stream=True, timeout=30)

        # Pick content-type or default to png
        content_type = resp.headers.get('Content-Type', 'image/png')

        # Return response content
        return HttpResponse(resp.content, content_type=content_type)

    except Exception as e:
        return JsonResponse({'error': f'Proxy error: {str(e)}'}, status=502)


def satellite_comparison_view(request):
    """View for satellite orbital parameter comparison"""
    return render(request, 'satellite_comparison.html')


def get_satellites_list(request):
    """API endpoint to get list of all satellites"""
    try:
        satellites = Satellite.objects.all().order_by('name')
        data = {
            'satellites': [
                {
                    'norad_id': sat.norad_id,
                    'name': sat.name,
                    'orbit': sat.orbit,
                    'inclination': sat.inclination,
                    'perigee': sat.perigee,
                    'apogee': sat.apogee,
                    'orbital_period': sat.orbital_period,
                    'status': sat.status
                }
                for sat in satellites
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def compare_satellites(request):
    """API endpoint to compare multiple satellites"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    try:
        import json
        data = json.loads(request.body)
        norad_ids = data.get('norad_ids', [])
        
        if not norad_ids:
            return JsonResponse({'error': 'No satellites selected'}, status=400)
        
        if len(norad_ids) > 10:
            return JsonResponse({'error': 'Maximum 10 satellites allowed'}, status=400)
        
        # Fetch satellites
        satellites = Satellite.objects.filter(norad_id__in=norad_ids)
        
        sat_data = []
        total_altitude = 0
        total_period = 0
        total_inclination = 0
        
        for sat in satellites:
            avg_altitude = (sat.perigee + sat.apogee) / 2 if sat.perigee and sat.apogee else 0
            total_altitude += avg_altitude
            total_period += sat.orbital_period if sat.orbital_period else 0
            total_inclination += sat.inclination if sat.inclination else 0
            
            sat_data.append({
                'norad_id': sat.norad_id,
                'name': sat.name,
                'satellite_type': sat.satellite_type,
                'orbit': sat.orbit,
                'inclination': sat.inclination,
                'orbital_period': sat.orbital_period,
                'perigee': sat.perigee,
                'apogee': sat.apogee,
                'orbits_per_day': sat.orbits_per_day,
                'launch_date': sat.launch_date.strftime('%Y-%m-%d') if sat.launch_date else None,
                'status': sat.status,
                'description': sat.description
            })
        
        count = len(sat_data)
        summary = {
            'count': count,
            'avg_altitude': total_altitude / count if count > 0 else 0,
            'avg_period': total_period / count if count > 0 else 0,
            'avg_inclination': total_inclination / count if count > 0 else 0
        }
        
        return JsonResponse({
            'satellites': sat_data,
            'summary': summary
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def tle_comparison_view(request):
    """View for TLE change comparison"""
    return render(request, 'tle_comparison.html')


def get_tle_comparison(request, norad_id):
    """API endpoint to compare current TLE with previous TLE"""
    try:
        satellite = Satellite.objects.get(norad_id=norad_id)
        
        # Get TLE history ordered by epoch date (newest first)
        tle_history = TLE.objects.filter(satellite=satellite).order_by('-epoch_date')
        
        if tle_history.count() < 2:
            return JsonResponse({
                'error': 'Not enough TLE data for comparison. Need at least 2 TLE records.'
            }, status=400)
        
        current_tle_obj = tle_history[0]
        previous_tle_obj = tle_history[1]
        
        # Parse TLE parameters
        def parse_tle(tle_text):
            """Parse TLE string and extract orbital parameters"""
            lines = tle_text.strip().split('\n')
            if len(lines) < 2:
                return None
            
            tle_line2 = lines[1] if len(lines) == 2 else lines[2] if len(lines) == 3 else lines[1]
            
            try:
                inclination = float(tle_line2[8:16].strip())
                ra_asc_node = float(tle_line2[17:25].strip())
                eccentricity = float('0.' + tle_line2[26:33].strip())
                arg_perigee = float(tle_line2[34:42].strip())
                mean_anomaly = float(tle_line2[43:51].strip())
                mean_motion = float(tle_line2[52:63].strip())
                
                # Calculate orbital parameters
                period = 1440.0 / mean_motion  # minutes
                semimajor_axis = (398600.4418 / ((mean_motion * 2 * 3.14159265359 / 86400) ** 2)) ** (1/3)
                
                apogee = semimajor_axis * (1 + eccentricity) - 6371
                perigee = semimajor_axis * (1 - eccentricity) - 6371
                
                return {
                    'inclination': inclination,
                    'ra_asc_node': ra_asc_node,
                    'eccentricity': eccentricity,
                    'arg_perigee': arg_perigee,
                    'mean_anomaly': mean_anomaly,
                    'mean_motion': mean_motion,
                    'period': period,
                    'apogee': apogee,
                    'perigee': perigee,
                    'semimajor_axis': semimajor_axis
                }
            except Exception as e:
                print(f"Error parsing TLE: {e}")
                return None
        
        current_params = parse_tle(current_tle_obj.tle)
        previous_params = parse_tle(previous_tle_obj.tle)
        
        if not current_params or not previous_params:
            return JsonResponse({'error': 'Error parsing TLE data'}, status=500)
        
        # Calculate changes
        def calculate_change(param_name, current, previous):
            absolute_change = current - previous
            percent_change = (absolute_change / previous * 100) if previous != 0 else 0
            
            return {
                'current': current,
                'previous': previous,
                'absolute_change': absolute_change,
                'percent_change': percent_change
            }
        
        changes = {
            'Inclination': calculate_change('inclination', 
                current_params['inclination'], previous_params['inclination']),
            'RA of Asc Node': calculate_change('ra_asc_node',
                current_params['ra_asc_node'], previous_params['ra_asc_node']),
            'Eccentricity': calculate_change('eccentricity',
                current_params['eccentricity'], previous_params['eccentricity']),
            'Arg of Perigee': calculate_change('arg_perigee',
                current_params['arg_perigee'], previous_params['arg_perigee']),
            'Mean Anomaly': calculate_change('mean_anomaly',
                current_params['mean_anomaly'], previous_params['mean_anomaly']),
            'Mean Motion': calculate_change('mean_motion',
                current_params['mean_motion'], previous_params['mean_motion']),
            'Orbital Period': calculate_change('period',
                current_params['period'], previous_params['period']),
            'Apogee': calculate_change('apogee',
                current_params['apogee'], previous_params['apogee']),
            'Perigee': calculate_change('perigee',
                current_params['perigee'], previous_params['perigee']),
            'Semimajor Axis': calculate_change('semimajor_axis',
                current_params['semimajor_axis'], previous_params['semimajor_axis'])
        }
        
        # Calculate days between updates
        days_between = (current_tle_obj.epoch_date - previous_tle_obj.epoch_date).total_seconds() / 86400
        
        # Get last 10 TLE records for history
        tle_history_data = []
        for tle in tle_history[:10]:
            params = parse_tle(tle.tle)
            if params:
                tle_history_data.append({
                    'epoch_date': tle.epoch_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'inclination': params['inclination'],
                    'period': params['period'],
                    'perigee': params['perigee'],
                    'apogee': params['apogee'],
                    'eccentricity': params['eccentricity']
                })
        
        return JsonResponse({
            'satellite': {
                'norad_id': satellite.norad_id,
                'name': satellite.name,
                'satellite_type': satellite.satellite_type,
                'orbit': satellite.orbit,
                'launch_date': satellite.launch_date.strftime('%Y-%m-%d') if satellite.launch_date else None,
                'status': satellite.status
            },
            'current_tle': {
                'epoch_date': current_tle_obj.epoch_date.strftime('%Y-%m-%d %H:%M:%S'),
                'parameters': current_params
            },
            'previous_tle': {
                'epoch_date': previous_tle_obj.epoch_date.strftime('%Y-%m-%d %H:%M:%S'),
                'parameters': previous_params
            },
            'changes': changes,
            'days_between_updates': days_between,
            'total_tle_count': tle_history.count(),
            'tle_history': tle_history_data
        })
        
    except Satellite.DoesNotExist:
        return JsonResponse({'error': 'Satellite not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
