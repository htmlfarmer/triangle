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
# --- Single Source of Truth for City Data ---
# This list is used for both exact lookups and as a fallback for finding the
# nearest city when online services are unavailable.
# Format: (City, Country, Latitude, Longitude)
# ==============================================================================
WORLD_CITIES = [
    ("New York", "USA", 40.7128, -74.0060),
    ("Los Angeles", "USA", 34.0522, -118.2437),
    ("Chicago", "USA", 41.8781, -87.6298),
    ("Houston", "USA", 29.7604, -95.3698),
    ("Phoenix", "USA", 33.4484, -112.0740),
    ("London", "UK", 51.5074, -0.1278),
    ("Tokyo", "Japan", 35.6895, 139.6917),
    ("Moscow", "Russia", 55.7558, 37.6176),
    ("Cairo", "Egypt", 30.0444, 31.2357),
    ("Beijing", "China", 39.9042, 116.4074),
    ("Sydney", "Australia", -33.8688, 151.2093),
    ("São Paulo", "Brazil", -23.5505, -46.6333),
    ("Mexico City", "Mexico", 19.4326, -99.1332),
    ("Mumbai", "India", 19.0760, 72.8777),
    ("Istanbul", "Turkey", 41.0082, 28.9784),
    ("Abu Dhabi", "UAE", 24.4539, 54.3773),
    ("Abuja", "Nigeria", 9.0765, 7.3986),
    ("Accra", "Ghana", 5.6037, -0.1870),
    ("Addis Ababa", "Ethiopia", 9.0300, 38.7400),
    ("Algiers", "Algeria", 36.7750, 3.0589),
    ("Amman", "Jordan", 31.9539, 35.9106),
    ("Amsterdam", "Netherlands", 52.3676, 4.9041),
    ("Ankara", "Turkey", 39.9334, 32.8597),
    ("Antananarivo", "Madagascar", -18.8792, 47.5079),
    ("Asuncion", "Paraguay", -25.2637, -57.5759),
    ("Athens", "Greece", 37.9838, 23.7275),
    ("Baghdad", "Iraq", 33.3152, 44.3661),
    ("Baku", "Azerbaijan", 40.4093, 49.8671),
    ("Bamako", "Mali", 12.6392, -8.0029),
    ("Bangkok", "Thailand", 13.7563, 100.5018),
    ("Bangui", "Central African Republic", 4.3947, 18.5582),
    ("Beirut", "Lebanon", 33.8938, 35.5018),
    ("Belgrade", "Serbia", 44.7866, 20.4489),
    ("Berlin", "Germany", 52.5200, 13.4050),
    ("Bern", "Switzerland", 46.9480, 7.4474),
    ("Bogota", "Colombia", 4.7110, -74.0721),
    ("Brasilia", "Brazil", -15.8267, -47.9218),
    ("Bratislava", "Slovakia", 48.1486, 17.1077),
    ("Brazzaville", "Congo", -4.2634, 15.2429),
    ("Brussels", "Belgium", 50.8503, 4.3517),
    ("Bucharest", "Romania", 44.4268, 26.1025),
    ("Budapest", "Hungary", 47.4979, 19.0402),
    ("Buenos Aires", "Argentina", -34.6037, -58.3816),
    ("Canberra", "Australia", -35.2809, 149.1300),
    ("Caracas", "Venezuela", 10.4806, -66.9036),
    ("Chisinau", "Moldova", 47.0105, 28.8638),
    ("Copenhagen", "Denmark", 55.6761, 12.5683),
    ("Dakar", "Senegal", 14.7167, -17.4677),
    ("Damascus", "Syria", 33.5138, 36.2765),
    ("Dhaka", "Bangladesh", 23.8103, 90.4125),
    ("Dili", "Timor-Leste", -8.5586, 125.5739),
    ("Djibouti", "Djibouti", 11.5890, 43.1450),
    ("Doha", "Qatar", 25.276987, 51.520008),
    ("Dublin", "Ireland", 53.3498, -6.2603),
    ("Dushanbe", "Tajikistan", 38.5598, 68.7870),
    ("Freetown", "Sierra Leone", 8.4844, -13.2299),
    ("Gaborone", "Botswana", -24.6282, 25.9231),
    ("Georgetown", "Guyana", 6.8013, -58.1551),
    ("Guatemala City", "Guatemala", 14.6349, -90.5069),
    ("Hanoi", "Vietnam", 21.0278, 105.8342),
    ("Harare", "Zimbabwe", -17.8252, 31.0335),
    ("Havana", "Cuba", 23.1136, -82.3666),
    ("Helsinki", "Finland", 60.1699, 24.9384),
    ("Islamabad", "Pakistan", 33.6844, 73.0479),
    ("Jakarta", "Indonesia", -6.2088, 106.8456),
    ("Jerusalem", "Israel", 31.7683, 35.2137),
    ("Juba", "South Sudan", 4.8594, 31.5713),
    ("Kabul", "Afghanistan", 34.5553, 69.2075),
    ("Kampala", "Uganda", 0.3476, 32.5825),
    ("Kathmandu", "Nepal", 27.7172, 85.3240),
    ("Khartoum", "Sudan", 15.5007, 32.5599),
    ("Kiev", "Ukraine", 50.4501, 30.5234),
    ("Kigali", "Rwanda", -1.9441, 30.0619),
    ("Kingston", "Jamaica", 17.9712, -76.7930),
    ("Kinshasa", "Congo", -4.4419, 15.2663),
    ("Kuala Lumpur", "Malaysia", 3.1390, 101.6869),
    ("Kuwait City", "Kuwait", 29.3759, 47.9774),
    ("La Paz", "Bolivia", -16.4897, -68.1193),
    ("Libreville", "Gabon", 0.4162, 9.4673),
    ("Lilongwe", "Malawi", -13.9626, 33.7741),
    ("Lima", "Peru", -12.0464, -77.0428),
    ("Lisbon", "Portugal", 38.7223, -9.1393),
    ("Ljubljana", "Slovenia", 46.0569, 14.5058),
    ("Lome", "Togo", 6.1319, 1.2228),
    ("Luanda", "Angola", -8.8399, 13.2894),
    ("Lusaka", "Zambia", -15.3875, 28.3228),
    ("Luxembourg", "Luxembourg", 49.6116, 6.1319),
    ("Madrid", "Spain", 40.4168, -3.7038),
    ("Malabo", "Equatorial Guinea", 3.7523, 8.7741),
    ("Male", "Maldives", 4.1755, 73.5093),
    ("Managua", "Nicaragua", 12.1150, -86.2362),
    ("Manama", "Bahrain", 26.2285, 50.5860),
    ("Manila", "Philippines", 14.5995, 120.9842),
    ("Maputo", "Mozambique", -25.9692, 32.5732),
    ("Maseru", "Lesotho", -29.3157, 27.4849),
    ("Mbabane", "Eswatini", -26.3054, 31.1367),
    ("Mecca", "Saudi Arabia", 21.3891, 39.8579),
    ("Minsk", "Belarus", 53.9045, 27.5615),
    ("Mogadishu", "Somalia", 2.0469, 45.3182),
    ("Monaco", "Monaco", 43.7384, 7.4246),
    ("Monrovia", "Liberia", 6.3007, -10.7958),
    ("Montevideo", "Uruguay", -34.9011, -56.1645),
    ("Moroni", "Comoros", -11.7022, 43.2541),
    ("Muscat", "Oman", 23.5859, 58.3829),
    ("N'Djamena", "Chad", 12.1348, 15.0557),
    ("Nairobi", "Kenya", -1.2921, 36.8219),
    ("Nassau", "Bahamas", 25.0470, -77.3554),
    ("Naypyidaw", "Myanmar", 19.7633, 96.0785),
    ("New Delhi", "India", 28.6139, 77.2090),
    ("Niamey", "Niger", 13.5116, 2.1254),
    ("Nicosia", "Cyprus", 35.1856, 33.3823),
    ("Nouakchott", "Mauritania", 18.0735, -15.9582),
    ("Nuku'alofa", "Tonga", -21.1393, -175.2048),
    ("Nur-Sultan", "Kazakhstan", 51.1694, 71.4491),
    ("Oslo", "Norway", 59.9139, 10.7522),
    ("Ottawa", "Canada", 45.4215, -75.6972),
    ("Ouagadougou", "Burkina Faso", 12.3714, -1.5197),
    ("Panama City", "Panama", 8.9824, -79.5199),
    ("Paramaribo", "Suriname", 5.8520, -55.2038),
    ("Paris", "France", 48.8566, 2.3522),
    ("Phnom Penh", "Cambodia", 11.5564, 104.9282),
    ("Podgorica", "Montenegro", 42.4304, 19.2594),
    ("Port Louis", "Mauritius", -20.1609, 57.5012),
    ("Port Moresby", "Papua New Guinea", -9.4431, 147.1803),
    ("Port-au-Prince", "Haiti", 18.5392, -72.3364),
    ("Port of Spain", "Trinidad and Tobago", 10.6548, -61.5097),
    ("Porto-Novo", "Benin", 6.4969, 2.6285),
    ("Prague", "Czech Republic", 50.0755, 14.4378),
    ("Praia", "Cabo Verde", 14.9330, -23.5133),
    ("Pretoria", "South Africa", -25.7479, 28.2293),
    ("Pyongyang", "North Korea", 39.0392, 125.7625),
    ("Quito", "Ecuador", -0.1807, -78.4678),
    ("Rabat", "Morocco", 34.0209, -6.8416),
    ("Reykjavik", "Iceland", 64.1466, -21.9426),
    ("Riga", "Latvia", 56.9496, 24.1052),
    ("Riyadh", "Saudi Arabia", 24.7136, 46.6753),
    ("Rome", "Italy", 41.9028, 12.4964),
    ("Roseau", "Dominica", 15.3013, -61.3882),
    ("San Jose", "Costa Rica", 9.9281, -84.0907),
    ("San Juan", "Puerto Rico", 18.4663, -66.1057),
    ("San Marino", "San Marino", 43.9424, 12.4578),
    ("San Salvador", "El Salvador", 13.6929, -89.2182),
    ("Sana'a", "Yemen", 15.3694, 44.1910),
    ("Santiago", "Chile", -33.4489, -70.6693),
    ("Santo Domingo", "Dominican Republic", 18.4861, -69.9312),
    ("Sao Tome", "Sao Tome and Principe", 0.3365, 6.7277),
    ("Sarajevo", "Bosnia and Herzegovina", 43.8563, 18.4131),
    ("Seoul", "South Korea", 37.5665, 126.9780),
    ("Singapore", "Singapore", 1.3521, 103.8198),
    ("Skopje", "North Macedonia", 41.9981, 21.4254),
    ("Sofia", "Bulgaria", 42.6977, 23.3219),
    ("Sri Jayawardenepura Kotte", "Sri Lanka", 6.9023, 79.8590),
    ("Stockholm", "Sweden", 59.3293, 18.0686),
    ("Sucre", "Bolivia", -19.0196, -65.2619),
    ("Suva", "Fiji", -18.1416, 178.4419),
    ("Taipei", "Taiwan", 25.0330, 121.5654),
    ("Tallinn", "Estonia", 59.4370, 24.7536),
    ("Tashkent", "Uzbekistan", 41.2995, 69.2401),
    ("Tbilisi", "Georgia", 41.7151, 44.8271),
    ("Tegucigalpa", "Honduras", 14.0723, -87.1921),
    ("Tehran", "Iran", 35.6892, 51.3890),
    ("Thimphu", "Bhutan", 27.4728, 89.6390),
    ("Tirana", "Albania", 41.3275, 19.8187),
    ("Tiraspol", "Moldova", 46.8403, 29.6105),
    ("Tripoli", "Libya", 32.8872, 13.1913),
    ("Tunis", "Tunisia", 36.8065, 10.1815),
    ("Ulaanbaatar", "Mongolia", 47.9179, 106.8833),
    ("Vaduz", "Liechtenstein", 47.1410, 9.5215),
    ("Valletta", "Malta", 35.8989, 14.5146),
    ("Victoria", "Seychelles", -4.6236, 55.4520),
    ("Vienna", "Austria", 48.2082, 16.3738),
    ("Vientiane", "Laos", 17.9748, 102.6309),
    ("Vilnius", "Lithuania", 54.6872, 25.2797),
    ("Warsaw", "Poland", 50.04969, 19.944544),
    ("Washington, D.C.", "USA", 38.9072, -77.0369),
    ("Wellington", "New Zealand", -41.2865, 174.7762),
    ("Windhoek", "Namibia", -22.5594, 17.0832),
    ("Yamoussoukro", "Côte d'Ivoire", 6.8206, -5.2768),
    ("Yaounde", "Cameroon", 3.8480, 11.5021),
    ("Yerevan", "Armenia", 40.1792, 44.4991),
    ("Zagreb", "Croatia", 45.8150, 15.9819)
]

# Create a dictionary for fast, exact-match lookups from the master list.
CITIES = {f"{city}, {country}": (lat, lon) for city, country, lat, lon in WORLD_CITIES}
# ==============================================================================

class LocalPrayerCalculator:
    """The Artisan's Astrolabe: Calculates prayer times from first principles."""
    def __init__(self, latitude, longitude, timezone_str, madhab, fajr_angle, isha_angle):
        self.lat = latitude; self.lon = longitude; self.tz_str = timezone_str
        self.madhab = madhab; self.fajr_angle = fajr_angle; self.isha_angle = isha_angle
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
        lat_rad = math.radians(self.lat); dec_rad = math.radians(declination); angle_rad = math.radians(angle)
        try: hour_angle = math.degrees(math.acos((math.sin(angle_rad) - math.sin(lat_rad) * math.sin(dec_rad)) / (math.cos(lat_rad) * math.cos(dec_rad))))
        except ValueError: return None
        if is_sunrise: hour_angle = -hour_angle
        transit = 12 - (self.lon / 15.0) - eot
        return transit + (hour_angle / 15.0)
    def calculate_times_for_date(self, dt_local):
        dt_utc = dt_local.astimezone(pytz.utc)
        julian_date = self._get_julian_date(dt_utc)
        declination, eot = self._calculate_sun_position(julian_date)
        transit_utc_hour = 12 - (self.lon / 15.0) - eot
        dhuhr_time_utc = dt_utc.replace(hour=0, minute=0, second=0) + timedelta(hours=transit_utc_hour)
        fajr_utc_hour = self._calculate_time_from_angle(-self.fajr_angle, declination, eot, is_sunrise=True)
        isha_utc_hour = self._calculate_time_from_angle(-self.isha_angle, declination, eot)
        sunrise_angle = -0.833
        sunrise_utc_hour = self._calculate_time_from_angle(sunrise_angle, declination, eot, is_sunrise=True)
        maghrib_utc_hour = self._calculate_time_from_angle(sunrise_angle, declination, eot)
        civil = 6.0; nautical = 12.0; astronomical = 18.0
        dawn_civil_utc = self._calculate_time_from_angle(-civil, declination, eot, is_sunrise=True)
        dusk_civil_utc = self._calculate_time_from_angle(-civil, declination, eot)
        dawn_nautical_utc = self._calculate_time_from_angle(-nautical, declination, eot, is_sunrise=True)
        dusk_nautical_utc = self._calculate_time_from_angle(-nautical, declination, eot)
        dawn_astro_utc = self._calculate_time_from_angle(-astronomical, declination, eot, is_sunrise=True)
        dusk_astro_utc = self._calculate_time_from_angle(-astronomical, declination, eot)
        shadow_length = 1 if self.madhab == 'shafi' else 2
        asr_angle = math.degrees(math.atan(1 / (shadow_length + math.tan(math.radians(abs(self.lat - declination))))))
        asr_utc_hour = self._calculate_time_from_angle(asr_angle, declination, eot)
        def to_local(utc_hour):
            if utc_hour is None: return None
            base_date = dt_utc.replace(hour=0, minute=0, second=0)
            return (base_date + timedelta(hours=utc_hour)).astimezone(pytz.timezone(self.tz_str))
        sunrise_dt = to_local(sunrise_utc_hour)
        maghrib_dt = to_local(maghrib_utc_hour)
        day_length = None
        if sunrise_dt and maghrib_dt:
            day_length = maghrib_dt - sunrise_dt
        return {
            "fajr": to_local(fajr_utc_hour), "sunrise": sunrise_dt, "dhuhr": dhuhr_time_utc.astimezone(pytz.timezone(self.tz_str)),
            "asr": to_local(asr_utc_hour), "maghrib": maghrib_dt, "isha": to_local(isha_utc_hour), "day_length": day_length,
        }

def get_location_by_ip():
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        data = response.json(); lat, lon = data['loc'].split(',')
        tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=float(lon), lat=float(lat))
        return {"latitude": float(lat), "longitude": float(lon), "timezone": timezone_str, "address": f"Current Location ({data.get('city', 'Unknown')})"}
    except requests.exceptions.ConnectionError:
        print("Offline: Could not connect to IP location service.")
        return None
    except Exception: return None

def get_location_by_address(city, state, country):
    city_key = f"{city}, {country}"
    if city_key in CITIES:
        lat, lon = CITIES[city_key]
        tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=lon, lat=lat)
        return {"latitude": lat, "longitude": lon, "timezone": timezone_str, "address": city_key}
    try:
        geolocator = Nominatim(user_agent="cosmic_compass")
        address_str = ", ".join(filter(None, [city, state, country]))
        location = geolocator.geocode(address_str, timeout=5)
        if location:
            tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return {"latitude": location.latitude, "longitude": location.longitude, "timezone": timezone_str, "address": location.address}
    except GeocoderServiceError:
        print(f"Offline: Could not connect to geocoding service for {address_str}.")
        return None
    except Exception: return None

def get_location_by_coords(lat, lon):
    if lat is None or lon is None or str(lat).strip() == "" or str(lon).strip() == "": return None
    try:
        lat_f = float(lat); lon_f = float(lon)
        tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=lon_f, lat=lat_f)
        if timezone_str:
            return {"latitude": lat_f, "longitude": lon_f, "timezone": timezone_str, "address": f"Coordinates ({lat_f}, {lon_f})"}
    except Exception: return None

def calculate_moon_mysteries(eph, observer, ts, t0, t1, tz):
    now_dt = t0.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)
    day_start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    # --- PERFORMANCE OPTIMIZATION ---
    # Search a smaller, more targeted window for events. +/- 2 days is fast
    # and sufficient to find the nearest events for any given day.
    search_start = ts.from_datetime(day_start - timedelta(days=2))
    search_end = ts.from_datetime(day_end + timedelta(days=2))

    def _to_dt(t): return t.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)

    moon_times = {"rise": None, "transit": None, "set": None}
    try:
        # Rise and Set
        is_up = almanac.risings_and_settings(eph, eph['moon'], observer)
        times_up, states_up = almanac.find_discrete(search_start, search_end, is_up)
        rise_list = [_to_dt(t) for t, s in zip(times_up, states_up) if s]
        set_list = [_to_dt(t) for t, s in zip(times_up, states_up) if not s]
        # Transit
        mer = almanac.meridian_transits(eph, eph['moon'], observer)
        times_mer, _ = almanac.find_discrete(search_start, search_end, mer)
        transit_list = [_to_dt(t) for t in times_mer]

        def choose_best(events):
            if not events: return None
            for e in events:
                if day_start <= e < day_end: return e
            midpoint = day_start + timedelta(hours=12)
            return min(events, key=lambda x: abs((x - midpoint).total_seconds()))

        moon_times['rise'] = choose_best(rise_list)
        moon_times['transit'] = choose_best(transit_list)
        moon_times['set'] = choose_best(set_list)
    except Exception: pass
    
    # Estimate 45-degree crossings based on rise/transit/set times
    ascent_45, descent_45 = None, None
    try:
        if moon_times.get('rise') and moon_times.get('transit'):
            ascent_45 = moon_times['rise'] + (moon_times['transit'] - moon_times['rise']) / 2
        if moon_times.get('transit') and moon_times.get('set'):
            descent_45 = moon_times['transit'] + (moon_times['set'] - moon_times['transit']) / 2
    except Exception: pass
    moon_times['ascent_45'] = ascent_45
    moon_times['descent_45'] = descent_45
    return moon_times

def format_time(dt_object):
    return dt_object.strftime('%I:%M %p') if dt_object else "Does not occur"

def subpoint_of_body(eph, body, t):
    try:
        app = eph['earth'].at(t).observe(eph[body]).apparent()
        lat, lon, _ = app.frame_latlon(itrs)
        lon_deg = lon.degrees
        if lon_deg > 180.0: lon_deg -= 360.0
        return lat.degrees, lon_deg
    except Exception:
        try:
            sp = eph['earth'].at(t).observe(eph[body]).apparent().subpoint()
            return sp.latitude.degrees, sp.longitude.degrees
        except Exception: return None, None

def nearest_city_for(lat, lon):
    try:
        geolocator = Nominatim(user_agent="cosmic_compass")
        loc = geolocator.reverse(f"{lat}, {lon}", zoom=10, timeout=5)
        if loc:
            addr = loc.raw.get('address', {})
            name = addr.get('city') or addr.get('town') or addr.get('village')
            country = addr.get('country')
            if name and country: return f"{name}, {country}"
    except (GeocoderServiceError, GeocoderTimedOut, Exception):
        # Fallback to local list if online service fails or is unavailable
        pass
    def haversine_km(a_lat, a_lon, b_lat, b_lon):
        R = 6371.0
        phi1, phi2 = math.radians(a_lat), math.radians(b_lat)
        dphi = math.radians(b_lat - a_lat)
        dlambda = math.radians(b_lon - a_lon)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    best_city, best_dist = None, float('inf')
    for city, country, clat, clon in WORLD_CITIES:
        dist = haversine_km(lat, lon, clat, clon)
        if dist < best_dist:
            best_dist, best_city = dist, f"{city}, {country} (~{int(dist)} km)"
    return best_city

if __name__ == "__main__":
    location = None
    mode = (LOCATION_MODE or "").strip().upper()
    if mode == "AUTO":
        location = get_location_by_ip()
        if not location: # Fallback if IP lookup fails
            location = get_location_by_address(CITY, STATE, COUNTRY)
    elif mode == "COORDS":
        location = get_location_by_coords(LATITUDE, LONGITUDE)
    else: # Default to ADDRESS mode
        location = get_location_by_address(CITY, STATE, COUNTRY)

    if not location:
        print("The cosmos remains veiled. Location could not be determined.")
    else:
        ts = load.timescale()
        eph = None
        local_bsp_file = 'de421.bsp'
        if os.path.exists(local_bsp_file):
            print("Found local de421.bsp file. Using it for calculations.")
            eph = load(local_bsp_file)
        else:
            print("Local de421.bsp not found. Attempting to download for future offline use...")
            try:
                eph = load('de421.bsp')
            except Exception as e:
                print(f"Warning: Could not download ephemeris ({e}). Moon data will be skipped.")
        
        observer = wgs84.latlon(location['latitude'], location['longitude'])
        tz = pytz.timezone(location['timezone']); now = datetime.now(tz)
        t0, t1 = ts.from_datetime(now), ts.from_datetime(now + timedelta(days=1))
        
        print(f"\n--- Qibla-Numa Report for: {location['address']} ---")
        
        sun_times = LocalPrayerCalculator(location['latitude'], location['longitude'], location['timezone'], MADHAB, PRAYER_METHOD_ANGLES['fajr'], PRAYER_METHOD_ANGLES['isha']).calculate_times_for_date(now)
        print("\n☀️ The Sun's Decree (Prayer Times)")
        print(f"   Fajr:    {format_time(sun_times['fajr'])}")
        print(f"   Sunrise: {format_time(sun_times['sunrise'])}")
        print(f"   Dhuhr:   {format_time(sun_times['dhuhr'])}")
        print(f"   Asr:     {format_time(sun_times['asr'])}")
        print(f"   Maghrib: {format_time(sun_times['maghrib'])}")
        print(f"   Isha:    {format_time(sun_times['isha'])}")
        
        if eph:
            moon_times = calculate_moon_mysteries(eph, observer, ts, t0, t1, tz)
            t_now = ts.from_datetime(now)
            apparent = (eph['earth'] + observer).at(t_now).observe(eph['moon']).apparent()
            alt, az, distance = apparent.altaz()

            print("\n🌙 The Moon's Mysteries (Local Time)")
            print(f"   Moonrise:    {format_time(moon_times['rise'])}")
            print(f"   Ascent 45°:  {format_time(moon_times['ascent_45'])}")
            print(f"   Zenith:      {format_time(moon_times['transit'])}")
            print(f"   Descent 45°: {format_time(moon_times['descent_45'])}")
            print(f"   Moonset:     {format_time(moon_times['set'])}")
            
            print("\n   Current Moon:")
            print(f"     Direction (azimuth): {alt.degrees:.2f}°")
            print(f"     Altitude:            {az.degrees:.2f}°")
            print(f"     Distance:            {distance.km:,.0f} km")
            
            phase_f = almanac.moon_phases(eph)
            phase_times, phase_vals = almanac.find_discrete(t0, ts.from_datetime(now + timedelta(days=35)), phase_f)
            upcoming_phases = sorted([{'name': almanac.MOON_PHASES[pv], 'date': pt.utc_datetime().astimezone(tz)} for pt, pv in zip(phase_times, phase_vals)], key=lambda x: x['date'])
            
            print('\n   Upcoming Primary Phases:')
            if upcoming_phases:
                for phase in upcoming_phases[:4]: # Show the next 4 phases
                    print(f"     {phase['name']:<15}: {phase['date'].strftime('%b %d, %Y, %I:%M %p')}")
            else:
                print("     Could not determine upcoming phases.")

            print('\nSub-point summary:')
            sun_lat, sun_lon = subpoint_of_body(eph, 'sun', t_now)
            moon_lat, moon_lon = subpoint_of_body(eph, 'moon', t_now)
            print(f"  Sun zenith (subsolar):  {sun_lat:.4f}, {sun_lon:.4f} — nearest: {nearest_city_for(sun_lat, sun_lon)}")
            print(f"  Moon zenith (sublunar): {moon_lat:.4f}, {moon_lon:.4f} — nearest: {nearest_city_for(moon_lat, moon_lon)}")
        else:
            print("\n🌙 Moon data unavailable (ephemeris file not found).")

        print("-" * 45)