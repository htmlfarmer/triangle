#!/usr/bin/env python3

import os
import pytz
import math
import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from skyfield.api import load, wgs84
from skyfield import almanac
from skyfield.framelib import itrs
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut, GeocoderServiceError

# ==============================================================================
# --- SANKALPA INSCRIPTION (THE SACRED DECREE) ---
# Carve your will here. The script will obey this Hukm (Command) without question.
# ==============================================================================

LOCATION_MODE = "" #"AUTO" 
CITY = "Moscow"
STATE = "Idaho"
COUNTRY = "USA"
LATITUDE = "" #28.6139
LONGITUDE = "" #77.2090
PRAYER_METHOD_ANGLES = {"fajr": 18.0, "isha": 18.0}
MADHAB = "hanafi"

# ==============================================================================
# --- FOR OFFLINE USE ---
# 1.  Download 'de421.bsp': Place this file in the same directory as the script.
#     You can get it from: https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp
# 2.  Set Location Manually: Set LOCATION_MODE to "ADDRESS" or "COORDS" and
#     provide the city/country or latitude/longitude above. This will prevent
#     any internet lookups for your location.
# ==============================================================================

# ==============================================================================
# --- Expanded City Database with Population ---
# Format: (City, Country, Latitude, Longitude, Population)
# ==============================================================================
WORLD_CITIES = [
    ("Tokyo", "Japan", 35.6895, 139.6917, 37435191), ("New Delhi", "India", 28.6139, 77.209, 29399141),
    ("Shanghai", "China", 31.2304, 121.4737, 26317104), ("São Paulo", "Brazil", -23.5505, -46.6333, 21846507),
    ("Mumbai", "India", 19.076, 72.8777, 20185064), ("Beijing", "China", 39.9042, 116.4074, 20035455),
    ("Cairo", "Egypt", 30.0444, 31.2357, 20484965), ("Dhaka", "Bangladesh", 23.8103, 90.4125, 20283552),
    ("Mexico City", "Mexico", 19.4326, -99.1332, 21671908), ("Osaka", "Japan", 34.6937, 135.5023, 19222665),
    ("Karachi", "Pakistan", 24.8607, 67.0011, 15741000), ("Chongqing", "China", 29.563, 106.5516, 15354000),
    ("Istanbul", "Turkey", 41.0082, 28.9784, 15029231), ("Buenos Aires", "Argentina", -34.6037, -58.3816, 15057000),
    ("Kolkata", "India", 22.5726, 88.3639, 14755000), ("Kinshasa", "Congo", -4.4419, 15.2663, 13932000),
    ("Lagos", "Nigeria", 6.5244, 3.3792, 13904000), ("Manila", "Philippines", 14.5995, 120.9842, 13699000),
    ("Tianjin", "China", 39.3434, 117.3616, 13396000), ("Rio de Janeiro", "Brazil", -22.9068, -43.1729, 13374275),
    ("Guangzhou", "China", 23.1291, 113.2644, 13081000), ("Moscow", "Russia", 55.7558, 37.6176, 12615279),
    ("Shenzhen", "China", 22.5431, 114.0579, 12356000), ("Lahore", "Pakistan", 31.5204, 74.3587, 12188000),
    ("Bangalore", "India", 12.9716, 77.5946, 11883000), ("Paris", "France", 48.8566, 2.3522, 11017000),
    ("Bogota", "Colombia", 4.711, -74.0721, 10778000), ("Jakarta", "Indonesia", -6.2088, 106.8456, 10770487),
    ("Chennai", "India", 13.0827, 80.2707, 10729000), ("Lima", "Peru", -12.0464, -77.0428, 10555000),
    ("Bangkok", "Thailand", 13.7563, 100.5018, 10389000), ("New York", "USA", 40.7128, -74.006, 8398748),
    ("London", "UK", 51.5074, -0.1278, 8982000), ("Seoul", "South Korea", 37.5665, 126.978, 9776000)
]

CITIES = {f"{c[0]}, {c[1]}": (c[2], c[3]) for c in WORLD_CITIES}

class LocalPrayerCalculator:
    """Calculates prayer times from first principles."""
    def __init__(self, latitude, longitude, timezone_str, madhab, fajr_angle, isha_angle):
        self.lat, self.lon, self.tz_str = latitude, longitude, timezone_str
        self.madhab, self.fajr_angle, self.isha_angle = madhab, fajr_angle, isha_angle
    def _get_julian_date(self, dt):
        return (dt - datetime(2000, 1, 1, 12, 0, 0, tzinfo=pytz.utc)).total_seconds() / 86400.0
    def _calculate_sun_position(self, julian_date):
        mean_solar_anomaly = (357.5291 + 0.98560028 * julian_date) % 360
        mean_longitude = (280.459 + 0.98564736 * julian_date) % 360
        ecliptic_longitude = (mean_longitude + 1.915 * math.sin(math.radians(mean_solar_anomaly)) + 0.020 * math.sin(math.radians(2 * mean_solar_anomaly))) % 360
        obliquity = 23.439 - 0.00000036 * julian_date
        right_ascension = math.degrees(math.atan2(math.cos(math.radians(obliquity)) * math.sin(math.radians(ecliptic_longitude)), math.cos(math.radians(ecliptic_longitude))))
        declination = math.degrees(math.asin(math.sin(math.radians(obliquity)) * math.sin(math.radians(ecliptic_longitude))))
        equation_of_time = (mean_longitude / 15.0) - (right_ascension / 15.0)
        if (mean_longitude / 15.0) > 20 and (right_ascension / 15.0) < 4: equation_of_time += 24
        return declination, equation_of_time
    def _calculate_time_from_angle(self, angle, declination, eot, is_sunrise=False):
        lat_rad, dec_rad, angle_rad = math.radians(self.lat), math.radians(declination), math.radians(angle)
        try: hour_angle = math.degrees(math.acos((math.sin(angle_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / (math.cos(lat_rad) * math.cos(dec_rad))))
        except ValueError: return None
        if is_sunrise: hour_angle = -hour_angle
        transit = 12 - (self.lon / 15.0) - eot
        return transit + (hour_angle / 15.0)
    def calculate_times_for_date(self, dt_local):
        dt_utc = dt_local.astimezone(pytz.utc)
        def to_local(utc_hour):
            if utc_hour is None: return None
            return (dt_utc.replace(hour=0, minute=0, second=0) + timedelta(hours=utc_hour)).astimezone(pytz.timezone(self.tz_str))
        declination, eot = self._calculate_sun_position(self._get_julian_date(dt_utc))
        shadow_length = 2 if self.madhab == 'hanafi' else 1
        asr_angle = math.degrees(math.atan(1 / (shadow_length + math.tan(abs(math.radians(self.lat - declination))))))
        return {
            "fajr": to_local(self._calculate_time_from_angle(-self.fajr_angle, declination, eot, is_sunrise=True)),
            "sunrise": to_local(self._calculate_time_from_angle(-0.833, declination, eot, is_sunrise=True)),
            "dhuhr": to_local(12 - (self.lon / 15.0) - eot),
            "asr": to_local(self._calculate_time_from_angle(asr_angle, declination, eot)),
            "maghrib": to_local(self._calculate_time_from_angle(-0.833, declination, eot)),
            "isha": to_local(self._calculate_time_from_angle(-self.isha_angle, declination, eot)),
        }

def get_location_by_ip():
    try:
        data = requests.get('https://ipinfo.io/json', timeout=5).json()
        lat, lon = map(float, data['loc'].split(','))
        tf = TimezoneFinder()
        return {"latitude": lat, "longitude": lon, "timezone": tf.timezone_at(lng=lon, lat=lat), "address": f"Current Location ({data.get('city', 'Unknown')})"}
    except (requests.exceptions.ConnectionError, Exception): return None

def get_location_by_address(city, state, country):
    city_key = f"{city}, {country}"
    if city_key in CITIES:
        lat, lon = CITIES[city_key]
        tf = TimezoneFinder()
        return {"latitude": lat, "longitude": lon, "timezone": tf.timezone_at(lng=lon, lat=lat), "address": city_key}
    try:
        geolocator = Nominatim(user_agent="cosmic_compass")
        loc = geolocator.geocode(f"{city}, {state}, {country}", timeout=5)
        if loc:
            tf = TimezoneFinder()
            return {"latitude": loc.latitude, "longitude": loc.longitude, "timezone": tf.timezone_at(lng=loc.longitude, lat=loc.latitude), "address": loc.address}
    except (GeocoderServiceError, Exception): return None

def get_location_by_coords(lat, lon):
    if not all((lat, lon, str(lat).strip(), str(lon).strip())): return None
    try:
        lat_f, lon_f = float(lat), float(lon)
        tf = TimezoneFinder()
        tz_str = tf.timezone_at(lng=lon_f, lat=lat_f)
        if tz_str: return {"latitude": lat_f, "longitude": lon_f, "timezone": tz_str, "address": f"Coordinates ({lat_f}, {lon_f})"}
    except Exception: return None

def calculate_moon_mysteries(eph, observer, ts, t0, tz):
    now_dt, day_start = t0.astimezone(tz), t0.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    search_start_ts, search_end_ts = ts.from_datetime(day_start - timedelta(days=2)), ts.from_datetime(day_start + timedelta(days=2))
    def _to_dt(t): return t.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)
    
    moon_times = {"rise": None, "transit": None, "set": None, "ascent_45": None, "descent_45": None}
    try:
        def choose_best(events, start_day_dt):
            if not events: return None
            end_day_dt = start_day_dt + timedelta(days=1)
            for e in events:
                if start_day_dt <= e < end_day_dt: return e
            return min(events, key=lambda x: abs(x - (start_day_dt + timedelta(hours=12))))
        
        t_rise, y_rise = almanac.find_discrete(search_start_ts, search_end_ts, almanac.risings_and_settings(eph, eph['moon'], observer))
        moon_times['rise'], moon_times['set'] = choose_best([_to_dt(t) for t, y in zip(t_rise, y_rise) if y], day_start), choose_best([_to_dt(t) for t, y in zip(t_rise, y_rise) if not y], day_start)

        t_transit, _ = almanac.find_discrete(search_start_ts, search_end_ts, almanac.meridian_transits(eph, eph['moon'], observer))
        if t_transit:
            highest_transit = max(t_transit, key=lambda t: (eph['earth'] + observer).at(t).observe(eph['moon']).apparent().altaz()[0].degrees)
            moon_times['transit'] = _to_dt(highest_transit)
        
        def moon_above_45(t): return (eph['earth'] + observer).at(t).observe(eph['moon']).apparent().altaz()[0].degrees > 45.0
        moon_above_45.step_days = 0.05
        t_45, y_45 = almanac.find_discrete(search_start_ts, search_end_ts, moon_above_45)
        if moon_times['rise']: moon_times['ascent_45'] = next((_to_dt(t) for t, y in zip(t_45, y_45) if y and _to_dt(t) > moon_times['rise']), None)
        if moon_times['transit']: moon_times['descent_45'] = next((_to_dt(t) for t, y in zip(t_45, y_45) if not y and _to_dt(t) > moon_times['transit']), None)
    except Exception: pass
    return moon_times

def calculate_inland_tides(eph, observer, ts, target_date, tz):
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=tz)
    search_start_ts, search_end_ts = ts.from_datetime(day_start - timedelta(hours=12)), ts.from_datetime(day_start + timedelta(hours=36))
    def _to_dt(t): return t.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)
    
    tides = []
    try:
        # Find all lunar transits (upper and lower) which correspond to high tides
        t_transits, y_transits = almanac.find_discrete(search_start_ts, search_end_ts, almanac.meridian_transits(eph, eph['moon'], observer))
        high_tides = sorted([_to_dt(t) for t in t_transits])
        
        # Calculate low tides as the midpoints between high tides
        for i in range(len(high_tides) - 1):
            tides.append({'name': 'High Tide', 'time': high_tides[i]})
            low_tide_time = high_tides[i] + (high_tides[i+1] - high_tides[i]) / 2
            tides.append({'name': 'Low Tide', 'time': low_tide_time})
        if high_tides: tides.append({'name': 'High Tide', 'time': high_tides[-1]})

    except Exception: pass
    return sorted([t for t in tides if day_start <= t['time'] < day_start + timedelta(days=1)], key=lambda x: x['time'])

def format_time(dt_object): return dt_object.strftime('%I:%M %p') if dt_object else "Does not occur"
def subpoint_of_body(eph, body, t):
    try:
        lat, lon, _ = eph['earth'].at(t).observe(eph[body]).apparent().frame_latlon(itrs)
        lon_deg = lon.degrees - 360 if lon.degrees > 180 else lon.degrees
        return lat.degrees, lon_deg
    except Exception: return None, None
def analyze_sub_point_locations(target_lat, target_lon):
    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0; phi1, phi2 = math.radians(lat1), math.radians(lat2)
        a = math.sin(math.radians(lat2 - lat1)/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(math.radians(lon2 - lon1)/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    closest = min(WORLD_CITIES, key=lambda c: haversine_km(target_lat, target_lon, c[2], c[3]))
    nearby = [c for c in WORLD_CITIES if haversine_km(target_lat, target_lon, c[2], c[3]) <= 5000]
    northern, southern = [c for c in nearby if c[2] > 0], [c for c in nearby if c[2] < 0]
    pop_n, pop_s = max(northern, key=lambda c: c[4], default=None), max(southern, key=lambda c: c[4], default=None)
    
    def format_city(city_data, t_lat, t_lon):
        if not city_data: return "N/A"
        dist = haversine_km(t_lat, t_lon, city_data[2], city_data[3])
        return f"{city_data[0]}, {city_data[1]} (~{int(dist)} km)"

    return {'nearest': format_city(closest, target_lat, target_lon), 'populous_northern': format_city(pop_n, target_lat, target_lon), 'populous_southern': format_city(pop_s, target_lat, target_lon)}

def find_global_tide_locations(eph, ts):
    t0 = ts.now()
    moon_lat, moon_lon = subpoint_of_body(eph, 'moon', t0)
    sun_lat, sun_lon = subpoint_of_body(eph, 'sun', t0)
    
    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0; phi1, phi2 = math.radians(lat1), math.radians(lat2)
        a = math.sin(math.radians(lat2 - lat1)/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(math.radians(lon2 - lon1)/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    antipode_lon = (moon_lon + 180) % 360 - 180
    high_tide_points = [(moon_lat, moon_lon), (-moon_lat, antipode_lon), (sun_lat, sun_lon)]
    low_tide_points = [(0, (moon_lon + 90) % 360 - 180), (0, (moon_lon - 90) % 360 - 180)]
    
    def find_nearest_city_for_point(p_lat, p_lon):
        if p_lat is None: return None
        closest = min(WORLD_CITIES, key=lambda c: haversine_km(p_lat, p_lon, c[2], c[3]))
        return f"{closest[0]}, {closest[1]}"

    return {
        'high': list(filter(None, {find_nearest_city_for_point(lat, lon) for lat, lon in high_tide_points})),
        'low': list(filter(None, {find_nearest_city_for_point(lat, lon) for lat, lon in low_tide_points}))
    }

if __name__ == "__main__":
    mode = (LOCATION_MODE or "").strip().upper()
    location = (get_location_by_ip() if mode == "AUTO" else get_location_by_coords(LATITUDE, LONGITUDE)) or get_location_by_address(CITY, STATE, COUNTRY)
    if not location:
        print("The cosmos remains veiled. Location could not be determined.")
    else:
        ts, eph = load.timescale(), None
        try:
            eph = load('de421.bsp')
        except Exception:
            print("Local de421.bsp not found. Attempting to download for future offline use...")
            try: eph = load('de421.bsp')
            except Exception as e: print(f"Warning: Could not download ephemeris ({e}). Moon and Tide data will be skipped.")
        
        observer = wgs84.latlon(location['latitude'], location['longitude'])
        tz = pytz.timezone(location['timezone']); now = datetime.now(tz)
        t0 = ts.from_datetime(now)
        
        print(f"\n--- Qibla-Numa Report for: {location['address']} at {now.strftime('%I:%M %p')} ---")
        
        sun_times = LocalPrayerCalculator(
            latitude=location['latitude'], longitude=location['longitude'],
            timezone_str=location['timezone'], madhab=MADHAB,
            fajr_angle=PRAYER_METHOD_ANGLES['fajr'], isha_angle=PRAYER_METHOD_ANGLES['isha']
        ).calculate_times_for_date(now)

        prayer_events = [{'name': label, 'time': sun_times[key]} for key, label in {'fajr': 'Fajr', 'sunrise': 'Sunrise', 'dhuhr': 'Dhuhr', 'asr': 'Asr', 'maghrib': 'Maghrib', 'isha': 'Isha'}.items() if sun_times.get(key)]
        moon_events, tide_events = [], []
        
        if eph:
            moon_times = calculate_moon_mysteries(eph, observer, ts, t0, tz)
            moon_events = [{'name': label, 'time': moon_times[key]} for key, label in {'rise': 'Moonrise', 'ascent_45': 'Ascent 45°', 'transit': 'Zenith', 'descent_45': 'Descent 45°', 'set': 'Moonset'}.items() if moon_times.get(key)]
            tide_events = calculate_inland_tides(eph, observer, ts, now.date(), tz)

        def get_next_event(events, now_time):
            future = sorted([e for e in events if e['time'] > now_time], key=lambda x: x['time'])
            return future[0] if future else None

        next_prayer_event = get_next_event(prayer_events, now)
        next_moon_event = get_next_event(moon_events, now)
        next_tide_event = get_next_event(tide_events, now)
        
        print("\n☀️ The Sun's Decree (Prayer Times)")
        for event in prayer_events:
            print(f" {'* ' if next_prayer_event and event['time'] == next_prayer_event['time'] else '  '}{event['name']:<10}: {format_time(event['time'])}")
        
        if eph:
            print("\n🌙 The Moon's Mysteries (Local Time)")
            for event in moon_events:
                print(f" {'* ' if next_moon_event and event['time'] == next_moon_event['time'] else '  '}{event['name']:<12}: {format_time(event['time'])}")

            if tide_events:
                last_tide = max([t for t in tide_events if t['time'] <= now], key=lambda x: x['time'], default=None)
                current_state = "Rising" if last_tide and last_tide['name'] == 'Low Tide' else "Falling"
                print(f"\n🌊 Inland Tide (Theoretical) - Currently {current_state}")
                for tide in tide_events:
                    print(f" {'* ' if next_tide_event and tide['time'] == next_tide_event['time'] else '  '}{tide['name']:<12}: {format_time(tide['time'])}")

            apparent = (eph['earth'] + observer).at(t0).observe(eph['moon']).apparent()
            alt, az, distance = apparent.altaz()
            print("\n   Current Moon:")
            print(f"     Direction (azimuth): {az.degrees:.2f}°")
            print(f"     Altitude:            {alt.degrees:.2f}°")
            print(f"     Distance:            {distance.km:,.0f} km")
            
            def _to_dt(t): return t.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)
            phase_times, phase_vals = almanac.find_discrete(t0, ts.from_datetime(now + timedelta(days=35)), almanac.moon_phases(eph))
            unique_phases = sorted(list({almanac.MOON_PHASES[pv]: _to_dt(pt) for pt, pv in zip(phase_times, phase_vals)}.items()), key=lambda item: item[1])
            print('\n   Upcoming Primary Phases:')
            if unique_phases:
                for i, (name, date) in enumerate(unique_phases[:4]):
                    print(f"   {'* ' if i == 0 else '  '}{name:<15}: {date.strftime('%b %d, %Y, %I:%M %p')}")

            print('\nSub-point & Global Tide Summary:')
            sun_lat, sun_lon = subpoint_of_body(eph, 'sun', t0)
            moon_lat, moon_lon = subpoint_of_body(eph, 'moon', t0)
            sun_cities, moon_cities = analyze_sub_point_locations(sun_lat, sun_lon), analyze_sub_point_locations(moon_lat, moon_lon)
            global_tides = find_global_tide_locations(eph, ts)
            
            print(f"  Sun Zenith:  {sun_lat:.2f}, {sun_lon:.2f} | Nearest: {sun_cities['nearest']}")
            print(f"    > Populous North: {sun_cities['populous_northern']}")
            print(f"    > Populous South: {sun_cities['populous_southern']}")
            print(f"\n  Moon Zenith: {moon_lat:.2f}, {moon_lon:.2f} | Nearest: {moon_cities['nearest']}")
            print(f"    > Populous North: {moon_cities['populous_northern']}")
            print(f"    > Populous South: {moon_cities['populous_southern']}")
            print("\n  Global High Tides Near: " + ", ".join(global_tides['high']))
            print("  Global Low Tides Near:  " + ", ".join(global_tides['low']))
        else: print("\n🌙 Moon and Tide data unavailable (ephemeris file not found).")
        print("-" * 45)