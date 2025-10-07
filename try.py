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
    ("London", "UK", 51.5074, -0.1278, 8982000), ("Seoul", "South Korea", 37.5665, 126.978, 9776000),
    ("Nagoya", "Japan", 35.1815, 136.9066, 9557000), ("Ho Chi Minh City", "Vietnam", 10.8231, 106.6297, 8993000),
    ("Tehran", "Iran", 35.6892, 51.389, 8847000), ("Hong Kong", "China", 22.3193, 114.1694, 7497000),
    ("Los Angeles", "USA", 34.0522, -118.2437, 3990456), ("Madrid", "Spain", 40.4168, -3.7038, 6642000),
    ("Singapore", "Singapore", 1.3521, 103.8198, 5850342), ("Santiago", "Chile", -33.4489, -70.6693, 6724000),
    ("Riyadh", "Saudi Arabia", 24.7136, 46.6753, 7009100), ("Saint Petersburg", "Russia", 59.9311, 30.3609, 5384342),
    ("Sydney", "Australia", -33.8688, 151.2093, 5312163), ("Melbourne", "Australia", -37.8136, 144.9631, 5078193),
    ("Baghdad", "Iraq", 33.3152, 44.3661, 7144000), ("Toronto", "Canada", 43.6532, -79.3832, 2930000),
    ("Berlin", "Germany", 52.52, 13.405, 3645000), ("Rome", "Italy", 41.9028, 12.4964, 2872800),
    ("Chicago", "USA", 41.8781, -87.6298, 2705994), ("Houston", "USA", 29.7604, -95.3698, 2325502),
    ("Phoenix", "USA", 33.4484, -112.074, 1660272), ("Philadelphia", "USA", 39.9526, -75.1652, 1584138),
    ("Dallas", "USA", 32.7767, -96.797, 1345047), ("San Francisco", "USA", 37.7749, -122.4194, 883305),
    ("Boston", "USA", 42.3601, -71.0589, 694583), ("Washington, D.C.", "USA", 38.9072, -77.0369, 705749),
    ("Miami", "USA", 25.7617, -80.1918, 470914), ("Atlanta", "USA", 33.749, -84.388, 506811),
    ("Seattle", "USA", 47.6062, -122.3321, 744955), ("Denver", "USA", 39.7392, -104.9903, 716492),
    ("Vancouver", "Canada", 49.2827, -123.1207, 675218), ("Montreal", "Canada", 45.5017, -73.5673, 1780000),
    ("Calgary", "Canada", 51.0447, -114.0719, 1285711), ("Ottawa", "Canada", 45.4215, -75.6972, 994837),
    ("Johannesburg", "South Africa", -26.2041, 28.0473, 5635000), ("Cape Town", "South Africa", -33.9249, 18.4241, 4488545),
    ("Nairobi", "Kenya", -1.2921, 36.8219, 4397073), ("Addis Ababa", "Ethiopia", 9.03, 38.74, 3384569),
    ("Casablanca", "Morocco", 33.5731, -7.5898, 3359818), ("Accra", "Ghana", 5.6037, -0.187, 2291352),
    ("Algiers", "Algeria", 36.775, 3.0589, 2712944), ("Tunis", "Tunisia", 36.8065, 10.1815, 638845),
    ("Auckland", "New Zealand", -36.8485, 174.7633, 1657000), ("Wellington", "New Zealand", -41.2865, 174.7762, 212700),
    ("Perth", "Australia", -31.9505, 115.8605, 2059484), ("Brisbane", "Australia", -27.4698, 153.0251, 2280000),
    ("Adelaide", "Australia", -34.9285, 138.6007, 1345777), ("Canberra", "Australia", -35.2809, 149.13, 426704),
    ("Honolulu", "USA", 21.3069, -157.8583, 351792), ("Reykjavik", "Iceland", 64.1466, -21.9426, 131345),
    ("Helsinki", "Finland", 60.1699, 24.9384, 650058), ("Oslo", "Norway", 59.9139, 10.7522, 693494),
    ("Stockholm", "Sweden", 59.3293, 18.0686, 975904), ("Copenhagen", "Denmark", 55.6761, 12.5683, 623404),
    ("Dublin", "Ireland", 53.3498, -6.2603, 544107), ("Amsterdam", "Netherlands", 52.3676, 4.9041, 862965),
    ("Brussels", "Belgium", 50.8503, 4.3517, 1209000), ("Vienna", "Austria", 48.2082, 16.3738, 1897000),
    ("Prague", "Czech Republic", 50.0755, 14.4378, 1309000), ("Warsaw", "Poland", 50.0497, 19.9445, 1790658),
    ("Budapest", "Hungary", 47.4979, 19.0402, 1752286), ("Kiev", "Ukraine", 50.4501, 30.5234, 2962180),
    ("Bucharest", "Romania", 44.4268, 26.1025, 1836000), ("Athens", "Greece", 37.9838, 23.7275, 664046),
    ("Lisbon", "Portugal", 38.7223, -9.1393, 504718), ("Geneva", "Switzerland", 46.2044, 6.1432, 201818),
    ("Frankfurt", "Germany", 50.1109, 8.6821, 753056), ("Munich", "Germany", 48.1351, 11.582, 1472000),
    ("Barcelona", "Spain", 41.3851, 2.1734, 1620343), ("Abu Dhabi", "UAE", 24.4539, 54.3773, 1483000),
    ("Abuja", "Nigeria", 9.0765, 7.3986, 1235880), ("Amman", "Jordan", 31.9539, 35.9106, 4007526),
    ("Ankara", "Turkey", 39.9334, 32.8597, 5445026), ("Antananarivo", "Madagascar", -18.8792, 47.5079, 1275207),
    ("Asuncion", "Paraguay", -25.2637, -57.5759, 525252), ("Baku", "Azerbaijan", 40.4093, 49.8671, 2293100),
    ("Bamako", "Mali", 12.6392, -8.0029, 2713000), ("Bangui", "Central African Republic", 4.3947, 18.5582, 794000),
    ("Beirut", "Lebanon", 33.8938, 35.5018, 2000000), ("Belgrade", "Serbia", 44.7866, 20.4489, 1166763),
    ("Bern", "Switzerland", 46.948, 7.4474, 133883), ("Bratislava", "Slovakia", 48.1486, 17.1077, 437725),
    ("Brazzaville", "Congo", -4.2634, 15.2429, 1827000), ("Chisinau", "Moldova", 47.0105, 28.8638, 532513),
    ("Dakar", "Senegal", 14.7167, -17.4677, 1146052), ("Damascus", "Syria", 33.5138, 36.2765, 1711000),
    ("Dar es Salaam", "Tanzania", -6.7924, 39.2083, 4364541), ("Dili", "Timor-Leste", -8.5586, 125.5739, 222323),
    ("Djibouti", "Djibouti", 11.589, 43.145, 562000), ("Doha", "Qatar", 25.277, 51.52, 2382000),
    ("Dubai", "UAE", 25.2048, 55.2708, 3137000), ("Dushanbe", "Tajikistan", 38.5598, 68.787, 846400),
    ("Edinburgh", "UK", 55.9533, -3.1883, 488050), ("Freetown", "Sierra Leone", 8.4844, -13.2299, 1055964),
    ("Fortaleza", "Brazil", -3.7319, -38.5267, 2669342),("Gaborone", "Botswana", -24.6282, 25.9231, 231592), 
    ("Georgetown", "Guyana", 6.8013, -58.1551, 118369), ("Guatemala City", "Guatemala", 14.6349, -90.5069, 994938), 
    ("Hanoi", "Vietnam", 21.0278, 105.8342, 7785000), ("Harare", "Zimbabwe", -17.8252, 31.0335, 1485231), 
    ("Havana", "Cuba", 23.1136, -82.3666, 2117625), ("Juba", "South Sudan", 4.8594, 31.5713, 525953), 
    ("Kabul", "Afghanistan", 34.5553, 69.2075, 4222000), ("Kampala", "Uganda", 0.3476, 32.5825, 1680800), 
    ("Kathmandu", "Nepal", 27.7172, 85.324, 1424000), ("Khartoum", "Sudan", 15.5007, 32.5599, 5274321), 
    ("Kigali", "Rwanda", -1.9441, 30.0619, 859332), ("Kingston", "Jamaica", 17.9712, -76.793, 662433), 
    ("Kuwait City", "Kuwait", 29.3759, 47.9774, 2989000), ("La Paz", "Bolivia", -16.4897, -68.1193, 757184), 
    ("Libreville", "Gabon", 0.4162, 9.4673, 703904), ("Lilongwe", "Malawi", -13.9626, 33.7741, 989318), 
    ("Ljubljana", "Slovenia", 46.0569, 14.5058, 284355), ("Lome", "Togo", 6.1319, 1.2228, 837437), 
    ("Luanda", "Angola", -8.8399, 13.2894, 2571861), ("Lusaka", "Zambia", -15.3875, 28.3228, 1747152), 
    ("Luxembourg", "Luxembourg", 49.6116, 6.1319, 122273), ("Malabo", "Equatorial Guinea", 3.7523, 8.7741, 297000), 
    ("Male", "Maldives", 4.1755, 73.5093, 133412), ("Managua", "Nicaragua", 12.115, -86.2362, 1055247), 
    ("Manama", "Bahrain", 26.2285, 50.586, 157474), ("Maputo", "Mozambique", -25.9692, 32.5732, 1088449), 
    ("Maseru", "Lesotho", -29.3157, 27.4849, 330760), ("Mbabane", "Eswatini", -26.3054, 31.1367, 68000), 
    ("Mecca", "Saudi Arabia", 21.3891, 39.8579, 2042000), ("Minsk", "Belarus", 53.9045, 27.5615, 2020600), 
    ("Mogadishu", "Somalia", 2.0469, 45.3182, 2388000), ("Monaco", "Monaco", 43.7384, 7.4246, 38682), 
    ("Monrovia", "Liberia", 6.3007, -10.7958, 1021762), ("Montevideo", "Uruguay", -34.9011, -56.1645, 1319108), 
    ("Moroni", "Comoros", -11.7022, 43.2541, 62351), ("Muscat", "Oman", 23.5859, 58.3829, 1421409), 
    ("N'Djamena", "Chad", 12.1348, 15.0557, 993492), ("Nassau", "Bahamas", 25.047, -77.3554, 274400), 
    ("Naypyidaw", "Myanmar", 19.7633, 96.0785, 924608), ("Niamey", "Niger", 13.5116, 2.1254, 1292000), 
    ("Nicosia", "Cyprus", 35.1856, 33.3823, 310355), ("Nouakchott", "Mauritania", 18.0735, -15.9582, 958199), 
    ("Nuku'alofa", "Tonga", -21.1393, -175.2048, 23221), ("Nur-Sultan", "Kazakhstan", 51.1694, 71.4491, 1136008), 
    ("Ouagadougou", "Burkina Faso", 12.3714, -1.5197, 2453498), ("Panama City", "Panama", 8.9824, -79.5199, 880691), 
    ("Paramaribo", "Suriname", 5.852, -55.2038, 240924), ("Phnom Penh", "Cambodia", 11.5564, 104.9282, 2129371), 
    ("Podgorica", "Montenegro", 42.4304, 19.2594, 150977), ("Port Louis", "Mauritius", -20.1609, 57.5012, 148108), 
    ("Port Moresby", "Papua New Guinea", -9.4431, 147.1803, 364125), ("Port-au-Prince", "Haiti", 18.5392, -72.3364, 987311), 
    ("Port of Spain", "Trinidad and Tobago", 10.6548, -61.5097, 18036), ("Porto-Novo", "Benin", 6.4969, 2.6285, 264320), 
    ("Praia", "Cabo Verde", 14.933, -23.5133, 130271), ("Pretoria", "South Africa", -25.7479, 28.2293, 741652), 
    ("Pyongyang", "North Korea", 39.0392, 125.7625, 2870000), ("Quito", "Ecuador", -0.1807, -78.4678, 1607734), 
    ("Rabat", "Morocco", 34.0209, -6.8416, 577827), ("Riga", "Latvia", 56.9496, 24.1052, 632614), 
    ("Roseau", "Dominica", 15.3013, -61.3882, 14741), ("San Jose", "Costa Rica", 9.9281, -84.0907, 333980), 
    ("San Juan", "Puerto Rico", 18.4663, -66.1057, 342259), ("San Marino", "San Marino", 43.9424, 12.4578, 4211), 
    ("San Salvador", "El Salvador", 13.6929, -89.2182, 258754), ("Sana'a", "Yemen", 15.3694, 44.191, 2545000), 
    ("Santo Domingo", "Dominican Republic", 18.4861, -69.9312, 965040), ("Sao Tome", "Sao Tome and Principe", 0.3365, 6.7277, 71868), 
    ("Sarajevo", "Bosnia and Herzegovina", 43.8563, 18.4131, 275524), ("Skopje", "North Macedonia", 41.9981, 21.4254, 506926), 
    ("Sofia", "Bulgaria", 42.6977, 23.3219, 1241675), ("Sri Jayawardenepura Kotte", "Sri Lanka", 6.9023, 79.859, 115826), 
    ("Sucre", "Bolivia", -19.0196, -65.2619, 237480), ("Suva", "Fiji", -18.1416, 178.4419, 88271), 
    ("Taipei", "Taiwan", 25.033, 121.5654, 2646204), ("Tallinn", "Estonia", 59.437, 24.7536, 434562), 
    ("Tashkent", "Uzbekistan", 41.2995, 69.2401, 2485900), ("Tbilisi", "Georgia", 41.7151, 44.8271, 1118035), 
    ("Tegucigalpa", "Honduras", 14.0723, -87.1921, 990660), ("Thimphu", "Bhutan", 27.4728, 89.639, 114551), 
    ("Tirana", "Albania", 41.3275, 19.8187, 418495), ("Tiraspol", "Moldova", 46.8403, 29.6105, 133807), 
    ("Tripoli", "Libya", 32.8872, 13.1913, 1126000), ("Ulaanbaatar", "Mongolia", 47.9179, 106.8833, 1540000), 
    ("Vaduz", "Liechtenstein", 47.141, 9.5215, 5696), ("Valletta", "Malta", 35.8989, 14.5146, 6444), 
    ("Victoria", "Seychelles", -4.6236, 55.452, 26450), ("Vientiane", "Laos", 17.9748, 102.6309, 820000), 
    ("Vilnius", "Lithuania", 54.6872, 25.2797, 539043), ("Windhoek", "Namibia", -22.5594, 17.0832, 268132), 
    ("Yamoussoukro", "Côte d'Ivoire", 6.8206, -5.2768, 212670), ("Yaounde", "Cameroon", 3.848, 11.5021, 2765000), 
    ("Yerevan", "Armenia", 40.1792, 44.4991, 1075800), ("Zagreb", "Croatia", 45.815, 15.9819, 806341)
]

CITIES = {f"{c[0]}, {c[1]}": (c[2], c[3]) for c in WORLD_CITIES}

def haversine_km(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points on Earth."""
    R = 6371.0; phi1, phi2 = math.radians(lat1), math.radians(lat2)
    a = math.sin(math.radians(lat2 - lat1)/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(math.radians(lon2 - lon1)/2)**2
    return 2 * R * math.asin(math.sqrt(a))

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
        t_transits, _ = almanac.find_discrete(search_start_ts, search_end_ts, almanac.meridian_transits(eph, eph['moon'], observer))
        high_tides = sorted([_to_dt(t) for t in t_transits])
        
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
def analyze_sub_point_locations(target_lat, target_lon, eph, ts, body_name):
    t0 = ts.now()
    
    visible_cities = []
    for city_data in WORLD_CITIES:
        city_obs = wgs84.latlon(city_data[2], city_data[3])
        alt, _, _ = (eph['earth'] + city_obs).at(t0).observe(eph[body_name]).apparent().altaz()
        if alt.degrees > 0:
            visible_cities.append(city_data)
    
    if not visible_cities: visible_cities = WORLD_CITIES

    closest = min(visible_cities, key=lambda c: haversine_km(target_lat, target_lon, c[2], c[3]))
    
    northern, southern = [c for c in visible_cities if c[2] > 0], [c for c in visible_cities if c[2] < 0]
    
    def get_influence_score(city, t_lat, t_lon):
        dist = haversine_km(t_lat, t_lon, city[2], city[3])
        return city[4] / (dist**2) if dist > 1 else float('inf')

    def find_most_influenced(candidates, t_lat, t_lon, exclude=None):
        if exclude:
            candidates = [c for c in candidates if c[0] != exclude[0]]
        if not candidates: return None
        return max(candidates, key=lambda c: get_influence_score(c, t_lat, t_lon))

    pop_n = find_most_influenced(northern, target_lat, target_lon)
    if pop_n and pop_n[0] == closest[0]: # De-duplicate
        pop_n = find_most_influenced(northern, target_lat, target_lon, exclude=pop_n)

    pop_s = find_most_influenced(southern, target_lat, target_lon)
    if pop_s and pop_s[0] == closest[0]: # De-duplicate
        pop_s = find_most_influenced(southern, target_lat, target_lon, exclude=pop_s)
    
    def format_city(city_data, t_lat, t_lon):
        if not city_data: return "N/A"
        dist = haversine_km(t_lat, t_lon, city_data[2], city_data[3])
        return f"{city_data[0]}, {city_data[1]} (~{int(dist)} km)"

    return {'nearest': format_city(closest, target_lat, target_lon), 'most_influenced_north': format_city(pop_n, target_lat, target_lon), 'most_influenced_south': format_city(pop_s, target_lat, target_lon)}

def find_global_tide_locations(eph, ts):
    t0 = ts.now()
    moon_lat, moon_lon = subpoint_of_body(eph, 'moon', t0)
    sun_lat, sun_lon = subpoint_of_body(eph, 'sun', t0)
    
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
            sun_cities = analyze_sub_point_locations(sun_lat, sun_lon, eph, ts, 'sun') if sun_lat is not None else None
            moon_cities = analyze_sub_point_locations(moon_lat, moon_lon, eph, ts, 'moon') if moon_lat is not None else None
            global_tides = find_global_tide_locations(eph, ts)
            
            if sun_cities:
                print(f"  Sun Zenith:  {sun_lat:.2f}, {sun_lon:.2f} | Nearest: {sun_cities['nearest']}")
                print(f"    > Most Influenced (North): {sun_cities['most_influenced_north']}")
                print(f"    > Most Influenced (South): {sun_cities['most_influenced_south']}")
            if moon_cities:
                print(f"\n  Moon Zenith: {moon_lat:.2f}, {moon_lon:.2f} | Nearest: {moon_cities['nearest']}")
                print(f"    > Most Influenced (North): {moon_cities['most_influenced_north']}")
                print(f"    > Most Influenced (South): {moon_cities['most_influenced_south']}")
            
            print("\n  Global High Tides Near: " + ", ".join(global_tides['high']))
            print("  Global Low Tides Near:  " + ", ".join(global_tides['low']))
        else: print("\n🌙 Moon and Tide data unavailable (ephemeris file not found).")
        print("-" * 45)