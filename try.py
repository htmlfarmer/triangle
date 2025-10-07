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
    ("Gaborone", "Botswana", -24.6282, 25.9231, 231592), ("Georgetown", "Guyana", 6.8013, -58.1551, 118369),
    ("Guatemala City", "Guatemala", 14.6349, -90.5069, 994938), ("Hanoi", "Vietnam", 21.0278, 105.8342, 7785000),
    ("Harare", "Zimbabwe", -17.8252, 31.0335, 1485231), ("Havana", "Cuba", 23.1136, -82.3666, 2117625),
    ("Juba", "South Sudan", 4.8594, 31.5713, 525953), ("Kabul", "Afghanistan", 34.5553, 69.2075, 4222000),
    ("Kampala", "Uganda", 0.3476, 32.5825, 1680800), ("Kathmandu", "Nepal", 27.7172, 85.324, 1424000),
    ("Khartoum", "Sudan", 15.5007, 32.5599, 5274321), ("Kigali", "Rwanda", -1.9441, 30.0619, 859332),
    ("Kingston", "Jamaica", 17.9712, -76.793, 662433), ("Kuwait City", "Kuwait", 29.3759, 47.9774, 2989000),
    ("La Paz", "Bolivia", -16.4897, -68.1193, 757184), ("Libreville", "Gabon", 0.4162, 9.4673, 703904),
    ("Lilongwe", "Malawi", -13.9626, 33.7741, 989318), ("Ljubljana", "Slovenia", 46.0569, 14.5058, 284355),
    ("Lome", "Togo", 6.1319, 1.2228, 837437), ("Luanda", "Angola", -8.8399, 13.2894, 2571861),
    ("Lusaka", "Zambia", -15.3875, 28.3228, 1747152), ("Luxembourg", "Luxembourg", 49.6116, 6.1319, 122273),
    ("Malabo", "Equatorial Guinea", 3.7523, 8.7741, 297000), ("Male", "Maldives", 4.1755, 73.5093, 133412),
    ("Managua", "Nicaragua", 12.115, -86.2362, 1055247), ("Manama", "Bahrain", 26.2285, 50.586, 157474),
    ("Maputo", "Mozambique", -25.9692, 32.5732, 1088449), ("Maseru", "Lesotho", -29.3157, 27.4849, 330760),
    ("Mbabane", "Eswatini", -26.3054, 31.1367, 68000), ("Mecca", "Saudi Arabia", 21.3891, 39.8579, 2042000),
    ("Minsk", "Belarus", 53.9045, 27.5615, 2020600), ("Mogadishu", "Somalia", 2.0469, 45.3182, 2388000),
    ("Monaco", "Monaco", 43.7384, 7.4246, 38682), ("Monrovia", "Liberia", 6.3007, -10.7958, 1021762),
    ("Montevideo", "Uruguay", -34.9011, -56.1645, 1319108), ("Moroni", "Comoros", -11.7022, 43.2541, 62351),
    ("Muscat", "Oman", 23.5859, 58.3829, 1421409), ("N'Djamena", "Chad", 12.1348, 15.0557, 993492),
    ("Nassau", "Bahamas", 25.047, -77.3554, 274400), ("Naypyidaw", "Myanmar", 19.7633, 96.0785, 924608),
    ("Niamey", "Niger", 13.5116, 2.1254, 1292000), ("Nicosia", "Cyprus", 35.1856, 33.3823, 310355),
    ("Nouakchott", "Mauritania", 18.0735, -15.9582, 958199), ("Nuku'alofa", "Tonga", -21.1393, -175.2048, 23221),
    ("Nur-Sultan", "Kazakhstan", 51.1694, 71.4491, 1136008), ("Ouagadougou", "Burkina Faso", 12.3714, -1.5197, 2453498),
    ("Panama City", "Panama", 8.9824, -79.5199, 880691), ("Paramaribo", "Suriname", 5.852, -55.2038, 240924),
    ("Phnom Penh", "Cambodia", 11.5564, 104.9282, 2129371), ("Podgorica", "Montenegro", 42.4304, 19.2594, 150977),
    ("Port Louis", "Mauritius", -20.1609, 57.5012, 148108), ("Port Moresby", "Papua New Guinea", -9.4431, 147.1803, 364125),
    ("Port-au-Prince", "Haiti", 18.5392, -72.3364, 987311), ("Port of Spain", "Trinidad and Tobago", 10.6548, -61.5097, 18036),
    ("Porto-Novo", "Benin", 6.4969, 2.6285, 264320), ("Praia", "Cabo Verde", 14.933, -23.5133, 130271),
    ("Pretoria", "South Africa", -25.7479, 28.2293, 741652), ("Pyongyang", "North Korea", 39.0392, 125.7625, 2870000),
    ("Quito", "Ecuador", -0.1807, -78.4678, 1607734), ("Rabat", "Morocco", 34.0209, -6.8416, 577827),
    ("Riga", "Latvia", 56.9496, 24.1052, 632614), ("Roseau", "Dominica", 15.3013, -61.3882, 14741),
    ("San Jose", "Costa Rica", 9.9281, -84.0907, 333980), ("San Juan", "Puerto Rico", 18.4663, -66.1057, 342259),
    ("San Marino", "San Marino", 43.9424, 12.4578, 4211), ("San Salvador", "El Salvador", 13.6929, -89.2182, 258754),
    ("Sana'a", "Yemen", 15.3694, 44.191, 2545000), ("Santo Domingo", "Dominican Republic", 18.4861, -69.9312, 965040),
    ("Sao Tome", "Sao Tome and Principe", 0.3365, 6.7277, 71868), ("Sarajevo", "Bosnia and Herzegovina", 43.8563, 18.4131, 275524),
    ("Skopje", "North Macedonia", 41.9981, 21.4254, 506926), ("Sofia", "Bulgaria", 42.6977, 23.3219, 1241675),
    ("Sri Jayawardenepura Kotte", "Sri Lanka", 6.9023, 79.859, 115826), ("Sucre", "Bolivia", -19.0196, -65.2619, 237480),
    ("Suva", "Fiji", -18.1416, 178.4419, 88271), ("Taipei", "Taiwan", 25.033, 121.5654, 2646204),
    ("Tallinn", "Estonia", 59.437, 24.7536, 434562), ("Tashkent", "Uzbekistan", 41.2995, 69.2401, 2485900),
    ("Tbilisi", "Georgia", 41.7151, 44.8271, 1118035), ("Tegucigalpa", "Honduras", 14.0723, -87.1921, 990660),
    ("Thimphu", "Bhutan", 27.4728, 89.639, 114551), ("Tirana", "Albania", 41.3275, 19.8187, 418495),
    ("Tiraspol", "Moldova", 46.8403, 29.6105, 133807), ("Tripoli", "Libya", 32.8872, 13.1913, 1126000),
    ("Ulaanbaatar", "Mongolia", 47.9179, 106.8833, 1540000), ("Vaduz", "Liechtenstein", 47.141, 9.5215, 5696),
    ("Valletta", "Malta", 35.8989, 14.5146, 6444), ("Victoria", "Seychelles", -4.6236, 55.452, 26450),
    ("Vientiane", "Laos", 17.9748, 102.6309, 820000), ("Vilnius", "Lithuania", 54.6872, 25.2797, 539043),
    ("Windhoek", "Namibia", -22.5594, 17.0832, 268132), ("Yamoussoukro", "Côte d'Ivoire", 6.8206, -5.2768, 212670),
    ("Yaounde", "Cameroon", 3.848, 11.5021, 2765000), ("Yerevan", "Armenia", 40.1792, 44.4991, 1075800),
    ("Zagreb", "Croatia", 45.815, 15.9819, 806341)
]

# Create a dictionary for fast, exact-match lookups from the master list.
CITIES = {f"{c[0]}, {c[1]}": (c[2], c[3]) for c in WORLD_CITIES}
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

def calculate_moon_mysteries(eph, observer, ts, t0, tz):
    now_dt = t0.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)
    day_start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    search_start_ts = ts.from_datetime(day_start - timedelta(days=2))
    search_end_ts = ts.from_datetime(day_start + timedelta(days=2))

    def _to_dt(t): return t.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)

    moon_times = {"rise": None, "transit": None, "set": None, "ascent_45": None, "descent_45": None}

    try:
        # --- Rise, Set, Transit ---
        def choose_best(events, start_day_dt):
            if not events: return None
            # Prefer event within the 24-hour window of the start day
            end_day_dt = start_day_dt + timedelta(days=1)
            for e in events:
                if start_day_dt <= e < end_day_dt: return e
            # Otherwise, find the one closest to noon of that day
            midpoint = start_day_dt + timedelta(hours=12)
            return min(events, key=lambda x: abs((x - midpoint).total_seconds()))

        # Rise and Set
        f_rise = almanac.risings_and_settings(eph, eph['moon'], observer)
        t_rise, y_rise = almanac.find_discrete(search_start_ts, search_end_ts, f_rise)
        all_rises = [_to_dt(t) for t, y in zip(t_rise, y_rise) if y]
        all_sets = [_to_dt(t) for t, y in zip(t_rise, y_rise) if not y]
        moon_times['rise'] = choose_best(all_rises, day_start)
        moon_times['set'] = choose_best(all_sets, day_start)

        # Zenith (Upper Transit)
        f_transit = almanac.meridian_transits(eph, eph['moon'], observer)
        t_transit, _ = almanac.find_discrete(search_start_ts, search_end_ts, f_transit)
        
        # Find the transit with the highest altitude (the true zenith)
        highest_transit = None
        max_alt = -91
        for t in t_transit:
            alt, _, _ = (eph['earth'] + observer).at(t).observe(eph['moon']).apparent().altaz()
            if alt.degrees > max_alt:
                max_alt = alt.degrees
                highest_transit = _to_dt(t)
        moon_times['transit'] = highest_transit

        # --- Accurate 45-Degree Crossing Calculation ---
        def moon_above_45(t):
            alt, _, _ = (eph['earth'] + observer).at(t).observe(eph['moon']).apparent().altaz()
            return alt.degrees > 45.0
        
        moon_above_45.step_days = 0.05
        t_45, y_45 = almanac.find_discrete(search_start_ts, search_end_ts, moon_above_45)
        
        # Find first ascent after rise, and first descent after transit
        if moon_times['rise']:
            for t, y in zip(t_45, y_45):
                event_time = _to_dt(t)
                if y and event_time > moon_times['rise']:
                    moon_times['ascent_45'] = event_time
                    break
        if moon_times['transit']:
            for t, y in zip(t_45, y_45):
                event_time = _to_dt(t)
                if not y and event_time > moon_times['transit']:
                    moon_times['descent_45'] = event_time
                    break
    except Exception: pass
    
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
    except Exception: return None, None

def analyze_sub_point_locations(target_lat, target_lon):
    """
    Finds three specific cities relative to a target lat/lon:
    1. The absolute nearest city.
    2. The most populous nearby city in the Northern Hemisphere.
    3. The most populous nearby city in the Southern Hemisphere.
    """
    POPULATION_SEARCH_RADIUS_KM = 5000

    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.asin(math.sqrt(a))

    # --- 1. Find Absolute Nearest City ---
    closest_city_overall = min(WORLD_CITIES, key=lambda c: haversine_km(target_lat, target_lon, c[2], c[3]))
    dist = haversine_km(target_lat, target_lon, closest_city_overall[2], closest_city_overall[3])
    nearest_result = f"{closest_city_overall[0]}, {closest_city_overall[1]} (~{int(dist)} km)"

    # --- 2. & 3. Find Most Populous Nearby Cities (N/S Hemispheres) ---
    nearby_cities = [c for c in WORLD_CITIES if haversine_km(target_lat, target_lon, c[2], c[3]) <= POPULATION_SEARCH_RADIUS_KM]
    nearby_northern = [c for c in nearby_cities if c[2] > 0]
    nearby_southern = [c for c in nearby_cities if c[2] < 0]
    
    populous_northern_result = "N/A"
    if nearby_northern:
        most_populous = max(nearby_northern, key=lambda c: c[4])
        dist = haversine_km(target_lat, target_lon, most_populous[2], most_populous[3])
        populous_northern_result = f"{most_populous[0]}, {most_populous[1]} (~{int(dist)} km)"

    populous_southern_result = "N/A"
    if nearby_southern:
        most_populous = max(nearby_southern, key=lambda c: c[4])
        dist = haversine_km(target_lat, target_lon, most_populous[2], most_populous[3])
        populous_southern_result = f"{most_populous[0]}, {most_populous[1]} (~{int(dist)} km)"

    return {
        'nearest': nearest_result,
        'populous_northern': populous_northern_result,
        'populous_southern': populous_southern_result,
    }

if __name__ == "__main__":
    location = None
    mode = (LOCATION_MODE or "").strip().upper()
    if mode == "AUTO":
        location = get_location_by_ip()
        if not location:
            location = get_location_by_address(CITY, STATE, COUNTRY)
    elif mode == "COORDS":
        location = get_location_by_coords(LATITUDE, LONGITUDE)
    else:
        location = get_location_by_address(CITY, STATE, COUNTRY)

    if not location:
        print("The cosmos remains veiled. Location could not be determined.")
    else:
        ts = load.timescale()
        eph = None
        local_bsp_file = 'de421.bsp'
        if os.path.exists(local_bsp_file):
            eph = load(local_bsp_file)
        else:
            print("Local de421.bsp not found. Attempting to download for future offline use...")
            try:
                eph = load('de421.bsp')
            except Exception as e:
                print(f"Warning: Could not download ephemeris ({e}). Moon data will be skipped.")
        
        observer = wgs84.latlon(location['latitude'], location['longitude'])
        tz = pytz.timezone(location['timezone']); now = datetime.now(tz)
        t0 = ts.from_datetime(now)
        
        print(f"\n--- Qibla-Numa Report for: {location['address']} at {now.strftime('%I:%M %p')} ---")
        
        sun_times = LocalPrayerCalculator(location['latitude'], location['longitude'], location['timezone'], MADHAB, PRAYER_METHOD_ANGLES['fajr'], PRAYER_METHOD_ANGLES['isha']).calculate_times_for_date(now)
        moon_times = calculate_moon_mysteries(eph, observer, ts, t0, tz) if eph else {}

        next_event_name = None
        all_events = []
        event_name_map = {
            'fajr': 'Fajr', 'sunrise': 'Sunrise', 'dhuhr': 'Dhuhr', 'asr': 'Asr', 'maghrib': 'Maghrib', 'isha': 'Isha',
            'rise': 'Moonrise', 'ascent_45': 'Ascent 45°', 'transit': 'Zenith', 'descent_45': 'Descent 45°', 'set': 'Moonset'
        }
        for name, dt in {**sun_times, **moon_times}.items():
            if dt and name in event_name_map:
                all_events.append({'name': event_name_map[name], 'time': dt})
        
        future_events = sorted([event for event in all_events if event['time'] > now], key=lambda x: x['time'])
        if future_events:
            next_event_name = future_events[0]['name']
        
        print("\n☀️ The Sun's Decree (Prayer Times)")
        for key, label in [('fajr','Fajr'), ('sunrise','Sunrise'), ('dhuhr','Dhuhr'), ('asr','Asr'), ('maghrib','Maghrib'), ('isha','Isha')]:
            prefix = "* " if label == next_event_name else "  "
            print(f" {prefix}{label:<10}: {format_time(sun_times.get(key))}")
        
        if eph:
            print("\n🌙 The Moon's Mysteries (Local Time)")
            for key, label in [('rise','Moonrise'), ('ascent_45','Ascent 45°'), ('transit','Zenith'), ('descent_45','Descent 45°'), ('set','Moonset')]:
                prefix = "* " if label == next_event_name else "  "
                print(f" {prefix}{label:<12}: {format_time(moon_times.get(key))}")

            t_now = ts.from_datetime(now)
            apparent = (eph['earth'] + observer).at(t_now).observe(eph['moon']).apparent()
            alt, az, distance = apparent.altaz()
            print("\n   Current Moon:")
            print(f"     Direction (azimuth): {az.degrees:.2f}°")
            print(f"     Altitude:            {alt.degrees:.2f}°")
            print(f"     Distance:            {distance.km:,.0f} km")
            
            phase_f = almanac.moon_phases(eph)
            phase_times, phase_vals = almanac.find_discrete(t0, ts.from_datetime(now + timedelta(days=35)), phase_f)
            unique_phases = []
            found_names = set()
            for pt, pv in zip(phase_times, phase_vals):
                name = almanac.MOON_PHASES[pv]
                if name not in found_names:
                    unique_phases.append({'name': name, 'date': pt.utc_datetime().astimezone(tz)})
                    found_names.add(name)
            
            print('\n   Upcoming Primary Phases:')
            if unique_phases:
                for i, phase in enumerate(unique_phases[:4]):
                    prefix = "* " if i == 0 else "  "
                    print(f"   {prefix}{phase['name']:<15}: {phase['date'].strftime('%b %d, %Y, %I:%M %p')}")
            else:
                print("     Could not determine upcoming phases.")

            print('\nSub-point summary:')
            sun_lat, sun_lon = subpoint_of_body(eph, 'sun', t_now)
            moon_lat, moon_lon = subpoint_of_body(eph, 'moon', t_now)
            
            sun_cities = analyze_sub_point_locations(sun_lat, sun_lon)
            moon_cities = analyze_sub_point_locations(moon_lat, moon_lon)

            print(f"  Sun zenith (subsolar):  {sun_lat:.4f}, {sun_lon:.4f}")
            print(f"    > Nearest:           {sun_cities['nearest']}")
            print(f"    > Populous (North):  {sun_cities['populous_northern']}")
            print(f"    > Populous (South):  {sun_cities['populous_southern']}")
            
            print(f"\n  Moon zenith (sublunar): {moon_lat:.4f}, {moon_lon:.4f}")
            print(f"    > Nearest:           {moon_cities['nearest']}")
            print(f"    > Populous (North):  {moon_cities['populous_northern']}")
            print(f"    > Populous (South):  {moon_cities['populous_southern']}")
        else:
            print("\n🌙 Moon data unavailable (ephemeris file not found).")

        print("-" * 45)