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
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut

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
        # twilight angles for civil/nautical/astronomical (degrees)
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
        # compute day length if sunrise and maghrib exist
        sunrise_dt = to_local(sunrise_utc_hour)
        maghrib_dt = to_local(maghrib_utc_hour)
        day_length = None
        if sunrise_dt and maghrib_dt:
            day_length = maghrib_dt - sunrise_dt

        return {
            "fajr": to_local(fajr_utc_hour),
            "dawn_civil": to_local(dawn_civil_utc),
            "dawn_nautical": to_local(dawn_nautical_utc),
            "dawn_astro": to_local(dawn_astro_utc),
            "sunrise": sunrise_dt,
            "dhuhr": dhuhr_time_utc.astimezone(pytz.timezone(self.tz_str)),
            "asr": to_local(asr_utc_hour),
            "maghrib": maghrib_dt,
            "dusk_civil": to_local(dusk_civil_utc),
            "dusk_nautical": to_local(dusk_nautical_utc),
            "dusk_astro": to_local(dusk_astro_utc),
            "isha": to_local(isha_utc_hour),
            "day_length": day_length,
        }

def get_location_by_ip():
    try:
        response = requests.get('https://ipinfo.io/json', timeout=10)
        data = response.json(); lat, lon = data['loc'].split(',')
        tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=float(lon), lat=float(lat))
        return {"latitude": float(lat), "longitude": float(lon), "timezone": timezone_str, "address": f"Current Location ({data.get('city', 'Unknown')})"}
    except Exception: return None

def get_location_by_address(city, state, country):
    # First, check our local list of cities for a quick lookup.
    city_key = f"{city}, {country}"
    if city_key in CITIES:
        lat, lon = CITIES[city_key]
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=lon, lat=lat)
        return {"latitude": lat, "longitude": lon, "timezone": timezone_str, "address": city_key}

    # If not in our local list, use the online geocoder.
    try:
        geolocator = Nominatim(user_agent="cosmic_compass")
        address_str = ", ".join(filter(None, [city, state, country]))
        location = geolocator.geocode(address_str, timeout=10)
        if location:
            tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            return {"latitude": location.latitude, "longitude": location.longitude, "timezone": timezone_str, "address": location.address}
    except Exception: return None

def get_location_by_coords(lat, lon):
    try:
        # If lat or lon are None or empty strings, caller likely wants to use
        # city/state/country lookup instead — treat those as missing here.
        if lat is None or lon is None: return None
        if isinstance(lat, str) and lat.strip() == "": return None
        if isinstance(lon, str) and lon.strip() == "": return None
        # ensure numeric types for timezone lookup
        lat_f = float(lat); lon_f = float(lon)
        tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=lon_f, lat=lat_f)
        if timezone_str:
            return {"latitude": lat_f, "longitude": lon_f, "timezone": timezone_str, "address": f"Coordinates ({lat_f}, {lon_f})"}
    except Exception: return None

def calculate_moon_mysteries(eph, observer, ts, t0, t1, tz):
    # Search over a much larger window around the local day to reliably find
    # rise/transit/set events and 45° altitude crossings. Some locations may
    # have events that occur near but outside the local day; expanding the
    # window helps us return a nearest reasonable event instead of None.
    now_dt = t0.utc_datetime().replace(tzinfo=pytz.utc).astimezone(tz)
    day_start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    # For rise/transit/set search +/-30 days; for 45° events +/-14 days
    search_start = ts.from_datetime(day_start - timedelta(days=30))
    search_end = ts.from_datetime(day_end + timedelta(days=30))

    def _to_dt(t):
        dt_utc = t.utc_datetime().replace(tzinfo=pytz.utc)
        return dt_utc.astimezone(tz)

    moon_times = {"rise": None, "transit": None, "set": None, "ascent_45": None, "descent_45": None}

    # Use risings_and_settings and meridian_transits to find rises/sets and meridian crossings
    try:
        is_up = almanac.risings_and_settings(eph, eph['moon'], observer)
        times_up, states_up = almanac.find_discrete(search_start, search_end, is_up)
        rise_list = []
        set_list = []
        for i in range(1, len(times_up)):
            prev_state = bool(states_up[i-1])
            cur_state = bool(states_up[i])
            # False -> True is a rise, True -> False is a set. Use the time at the transition.
            if not prev_state and cur_state:
                rise_list.append(_to_dt(times_up[i]))
            if prev_state and not cur_state:
                set_list.append(_to_dt(times_up[i]))

        # meridian crossings (transits / antitransits)
        mer = almanac.meridian_transits(eph, eph['moon'], observer)
        times_mer, states_mer = almanac.find_discrete(search_start, search_end, mer)
        # choose the upper transit (maximum altitude) among candidates
        transit_candidates = []
        for t_mer in times_mer:
            try:
                alt_deg = (eph['earth'] + observer).at(t_mer).observe(eph['moon']).apparent().altaz()[0].degrees
            except Exception:
                alt_deg = None
            transit_candidates.append(( _to_dt(t_mer), alt_deg ))
        transit_list = [dt for dt, alt in transit_candidates]

        def choose_best(events):
            if not events:
                return None
            for e in events:
                if e >= day_start and e < day_end:
                    return e
            midpoint = day_start + (day_end - day_start) / 2
            return min(events, key=lambda x: abs((x - midpoint).total_seconds()))

        moon_times['rise'] = choose_best(rise_list)
        # choose_best for transit should prefer the candidate with highest altitude
        def choose_best_transit(candidates):
            if not candidates:
                return None
            # candidates is list of (datetime, altitude)
            # prefer those inside the local day
            inside = [c for c in candidates if c[0] >= day_start and c[0] < day_end and c[1] is not None]
            if inside:
                # return the one with maximum altitude
                return max(inside, key=lambda x: x[1])[0]
            # otherwise pick the candidate with the largest altitude overall
            with_alt = [c for c in candidates if c[1] is not None]
            if with_alt:
                return max(with_alt, key=lambda x: x[1])[0]
            # fallback to nearest in time
            midpoint = day_start + (day_end - day_start) / 2
            return min([c[0] for c in candidates], key=lambda x: abs((x - midpoint).total_seconds()))

        moon_times['transit'] = choose_best_transit(transit_candidates)
        moon_times['set'] = choose_best(set_list)
    except Exception:
        pass

    # If almanac didn't produce events, fall back to a direct altitude sampling
    # scan over +/-2 days at 5-minute resolution to find crossings and transit.
    def _fallback_sampling():
        sample_start = day_start - timedelta(days=2)
        sample_end = day_end + timedelta(days=2)
        step = timedelta(minutes=5)
        times = []
        altitudes = []
        t = sample_start
        while t <= sample_end:
            sf_t = ts.from_datetime(t)
            try:
                alt = (eph['earth'] + observer).at(sf_t).observe(eph['moon']).apparent().altaz()[0].degrees
            except Exception:
                alt = None
            times.append(t); altitudes.append(alt)
            t = t + step

        # find horizon crossings (use horizon -0.5667 deg like risings_and_settings)
        horizon = -34.0/60.0
        rises = []
        sets = []
        for i in range(1, len(times)):
            a0 = altitudes[i-1]; a1 = altitudes[i]
            if a0 is None or a1 is None: continue
            if a0 < horizon and a1 >= horizon:
                # interpolate
                frac = (horizon - a0) / (a1 - a0) if (a1 - a0) != 0 else 0
                dt_cross = times[i-1] + (times[i] - times[i-1]) * frac
                rises.append(dt_cross)
            if a0 >= horizon and a1 < horizon:
                frac = (a0 - horizon) / (a0 - a1) if (a0 - a1) != 0 else 0
                dt_cross = times[i-1] + (times[i] - times[i-1]) * frac
                sets.append(dt_cross)

        # find transit (maximum altitude)
        max_alt = None; max_idx = None
        for i, a in enumerate(altitudes):
            if a is None: continue
            if max_alt is None or a > max_alt:
                max_alt = a; max_idx = i
        transit_dt = None
        if max_idx is not None:
            # parabolic refinement using neighbors if available
            if 0 < max_idx < len(altitudes)-1 and altitudes[max_idx-1] is not None and altitudes[max_idx+1] is not None:
                y1 = altitudes[max_idx-1]; y2 = altitudes[max_idx]; y3 = altitudes[max_idx+1]
                t1 = times[max_idx-1].timestamp(); t2 = times[max_idx].timestamp(); t3 = times[max_idx+1].timestamp()
                # vertex of parabola fit
                denom = (t1 - t2)*(t1 - t3)*(t2 - t3)
                if denom != 0:
                    A = (t3*(y2 - y1) + t2*(y1 - y3) + t1*(y3 - y2)) / denom
                    B = (t3*t3*(y1 - y2) + t2*t2*(y3 - y1) + t1*t1*(y2 - y3)) / denom
                    tv = -B/(2*A) if A != 0 else t2
                    transit_dt = datetime.fromtimestamp(tv, tz)
                else:
                    transit_dt = times[max_idx]
            else:
                transit_dt = times[max_idx]

        # 45 degree crossings
        asc45 = []; desc45 = []
        for i in range(1, len(times)):
            a0 = altitudes[i-1]; a1 = altitudes[i]
            if a0 is None or a1 is None: continue
            if a0 < 45.0 and a1 >= 45.0:
                frac = (45.0 - a0) / (a1 - a0) if (a1 - a0) != 0 else 0
                asc45.append(times[i-1] + (times[i] - times[i-1]) * frac)
            if a0 >= 45.0 and a1 < 45.0:
                frac = (a0 - 45.0) / (a0 - a1) if (a0 - a1) != 0 else 0
                desc45.append(times[i-1] + (times[i] - times[i-1]) * frac)

        return rises, transit_dt, sets, asc45, desc45

    # If still missing, use fallback sampling
    if not moon_times['rise'] or not moon_times['set'] or not moon_times['transit'] or not moon_times['ascent_45'] or not moon_times['descent_45']:
        try:
            rises_f, transit_f, sets_f, asc45_f, desc45_f = _fallback_sampling()
            def choose_best_dt(list_dt):
                if not list_dt: return None
                # pick one within the day if possible
                for d in list_dt:
                    if d >= day_start and d < day_end: return d
                midpoint = day_start + (day_end - day_start) / 2
                return min(list_dt, key=lambda x: abs((x - midpoint).total_seconds()))

            if not moon_times['rise']:
                moon_times['rise'] = choose_best_dt(rises_f)
            if not moon_times['set']:
                moon_times['set'] = choose_best_dt(sets_f)
            if not moon_times['transit']:
                moon_times['transit'] = transit_f
            if not moon_times['ascent_45']:
                moon_times['ascent_45'] = choose_best_dt(asc45_f)
            if not moon_times['descent_45']:
                moon_times['descent_45'] = choose_best_dt(desc45_f)
        except Exception:
            pass

    # Find times when the Moon's altitude crosses 45 degrees (above/below).
    # Use a smaller but still extended window for altitude crossings.
    alt_search_start = ts.from_datetime(day_start - timedelta(days=3))
    alt_search_end = ts.from_datetime(day_end + timedelta(days=3))
    def moon_above_45(t):
        alt = (eph['earth'] + observer).at(t).observe(eph['moon']).apparent().altaz()[0].degrees
        return alt > 45.0

    try:
        times45, events45 = almanac.find_discrete(alt_search_start, alt_search_end, moon_above_45)
        crossings = [_to_dt(t) for t in times45]
        ascent = None; descent = None

        # events45[i] is True if moon_above_45 is True after times45[i]. To detect
        # transitions we compare consecutive event states. An ascent is where
        # events45[i] is True and (i==0 or events45[i-1] is False). A descent is
        # where events45[i] is False and (i==0 or events45[i-1] is True).
        # determine initial state at the start of the search window to avoid
        # misclassifying the very first transition
        try:
            initial_state = bool(moon_above_45(alt_search_start))
        except Exception:
            initial_state = None

        for i, t_obj in enumerate(crossings):
            state = bool(events45[i])
            prev_state = bool(events45[i-1]) if i > 0 else initial_state
            if t_obj >= day_start and t_obj < day_end:
                if state and (prev_state is False) and ascent is None:
                    ascent = t_obj
                if (not state) and (prev_state is True) and descent is None:
                    descent = t_obj

        # If not found inside day, fall back to nearest crossings
        midpoint = day_start + (day_end - day_start) / 2
        if ascent is None and crossings:
            ascent = min(crossings, key=lambda x: abs((x - midpoint).total_seconds()))
        if descent is None and crossings:
            descent = min(crossings, key=lambda x: abs((x - midpoint).total_seconds()))

        moon_times['ascent_45'] = ascent
        moon_times['descent_45'] = descent
    except Exception:
        pass

    # Post-process around transit if available: prefer an ascent that occurs
    # before the transit and a descent after the transit to keep ordering
    try:
        tr = moon_times.get('transit')
        if tr is not None:
            window_start = tr - timedelta(days=1)
            window_end = tr + timedelta(days=1)
            t0w = ts.from_datetime(window_start); t1w = ts.from_datetime(window_end)
            times_w, events_w = almanac.find_discrete(t0w, t1w, moon_above_45)
            crossings_w = [_to_dt(t) for t in times_w]
            # compute initial state at window start
            try:
                init_state_w = bool(moon_above_45(ts.from_datetime(window_start)))
            except Exception:
                init_state_w = None

            asc_candidate = None; desc_candidate = None
            for i, cdt in enumerate(crossings_w):
                state = bool(events_w[i])
                prev_state = bool(events_w[i-1]) if i > 0 else init_state_w
                # ascent: False -> True; descent: True -> False
                if cdt <= tr and state and prev_state is False:
                    # keep latest ascent before transit
                    if asc_candidate is None or cdt > asc_candidate:
                        asc_candidate = cdt
                if cdt >= tr and (not state) and prev_state is True:
                    # keep earliest descent after transit
                    if desc_candidate is None or cdt < desc_candidate:
                        desc_candidate = cdt

            if asc_candidate:
                moon_times['ascent_45'] = asc_candidate
            if desc_candidate:
                moon_times['descent_45'] = desc_candidate
    except Exception:
        pass

    # If we have rise, transit and set for the day, prefer an ascent between
    # rise->transit and a descent between transit->set so times are from the
    # same observable event window.
    try:
        r = moon_times.get('rise'); tr = moon_times.get('transit'); s = moon_times.get('set')
        if r and tr and s:
            # small margins to ensure we include nearby crossings
            margin = timedelta(hours=1)
            t0a = ts.from_datetime(max(r - margin, day_start - timedelta(days=1)))
            t1a = ts.from_datetime(min(tr + margin, day_end + timedelta(days=1)))
            times_a, events_a = almanac.find_discrete(t0a, t1a, moon_above_45)
            crossings_a = [_to_dt(t) for t in times_a]
            # pick latest True crossing that is >= rise and <= transit
            asc = None
            for tt, ev in zip(crossings_a, events_a):
                if ev and tt >= r and tt <= tr:
                    asc = tt
            if asc:
                moon_times['ascent_45'] = asc

            t0d = ts.from_datetime(max(tr - margin, day_start - timedelta(days=1)))
            t1d = ts.from_datetime(min(s + margin, day_end + timedelta(days=1)))
            times_d, events_d = almanac.find_discrete(t0d, t1d, moon_above_45)
            crossings_d = [_to_dt(t) for t in times_d]
            desc = None
            for tt, ev in zip(crossings_d, events_d):
                if (not ev) and tt >= tr and tt <= s:
                    desc = tt
                    break
            if desc:
                moon_times['descent_45'] = desc
    except Exception:
        pass

    return moon_times

def format_time(dt_object):
    return dt_object.strftime('%I:%M %p') if dt_object else "Does not occur today"


def daily_moon_phase_names(eph, ts, start_dt, tz, days=30):
    """Return a list of (date, phase_name) for each day of the lunation starting at start_dt.

    start_dt should be a timezone-aware datetime in tz representing the new moon time (or any start).
    We sample once per day (local noon) and classify into one of 8 categories.
    """
    names = []
    # helper to get fraction illuminated at a given datetime
    def frac_at(dt):
        t = ts.from_datetime(dt.astimezone(pytz.utc))
        return almanac.fraction_illuminated(eph, 'moon', t)

    # sample each day at local noon to represent that day's phase
    for n in range(days):
        day_dt = (start_dt + timedelta(days=n)).replace(hour=12, minute=0, second=0, microsecond=0)
        f = frac_at(day_dt)
        # estimate slope by comparing to the previous half-day and next half-day
        f_prev = frac_at(day_dt - timedelta(hours=12))
        f_next = frac_at(day_dt + timedelta(hours=12))
        increasing = (f_next > f_prev)

        # classification thresholds
        if f < 0.02:
            phase = 'New Moon'
        elif f <= 0.49:
            phase = 'Waxing Crescent' if increasing else 'Waning Crescent'
        elif 0.49 < f < 0.51:
            phase = 'First Quarter' if increasing else 'Third Quarter'
        elif f <= 0.99:
            phase = 'Waxing Gibbous' if increasing else 'Waning Gibbous'
        else:
            phase = 'Full Moon'

        names.append((day_dt.date(), phase))

    return names


def subpoint_of_body(eph, body, t):
    """Return (lat, lon) of the subpoint of a solar-system body at Skyfield time t."""
    try:
        # Compute the apparent position as seen from Earth's center, then
        # convert into the Earth-fixed ITRS frame to obtain latitude/longitude.
        app = eph['earth'].at(t).observe(eph[body]).apparent()
        lat, lon, _ = app.frame_latlon(itrs)
        
        # --- FIX: Normalize longitude to the -180 to 180 degree range ---
        lon_deg = lon.degrees
        if lon_deg > 180.0:
            lon_deg -= 360.0
        
        return lat.degrees, lon_deg
    except Exception:
        # Fallback: compute the apparent subpoint as seen from Earth
        try:
            sp = eph['earth'].at(t).observe(eph[body]).apparent().subpoint()
            return sp.latitude.degrees, sp.longitude.degrees
        except Exception:
            return None, None


def nearest_city_for(lat, lon):
    """Use Nominatim reverse geocoding to get a nearby city name; return display string."""
    try:
        geolocator = Nominatim(user_agent="cosmic_compass")
        # Try a few zoom levels and timeouts to improve chances of finding a nearby locality
        for zoom, timeout in ((10, 10), (8, 8), (6, 6)):
            try:
                loc = geolocator.reverse(f"{lat}, {lon}", zoom=zoom, timeout=timeout)
            except TypeError:
                # some geopy versions have different signature; try without keywords
                loc = geolocator.reverse(f"{lat}, {lon}")
            except Exception:
                loc = None
            if loc:
                try:
                    addr = loc.raw.get('address', {})
                except Exception:
                    addr = {}
                name = None
                for key in ('city', 'town', 'village', 'hamlet', 'county'):
                    if addr.get(key):
                        name = addr.get(key)
                        break
                country = addr.get('country')
                if name and country:
                    return f"{name}, {country}"
                if name:
                    return name
                if country:
                    return country
                # fallback to display_name when available
                try:
                    dn = loc.raw.get('display_name')
                    if dn:
                        return dn
                except Exception:
                    pass
        # If reverse geocoding didn't return anything useful, fall back to our
        # master offline city list.
        def haversine_km(a_lat, a_lon, b_lat, b_lon):
            import math
            R = 6371.0
            phi1 = math.radians(a_lat); phi2 = math.radians(b_lat)
            dphi = math.radians(b_lat - a_lat); dlambda = math.radians(b_lon - a_lon)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return 2 * R * math.asin(math.sqrt(a))
            
        best = None; best_d = None
        # --- MODIFICATION: Use the master WORLD_CITIES list ---
        for city, country, clat, clon in WORLD_CITIES:
            d = haversine_km(lat, lon, clat, clon)
            if best_d is None or d < best_d:
                best = (city, country, d); best_d = d
        if best:
            return f"{best[0]}, {best[1]} (~{int(best[2])} km)"
    except (GeocoderUnavailable, GeocoderTimedOut, Exception):
        return None

if __name__ == "__main__":
    location = None
    # Normalize the mode; treat empty string ("") as ADDRESS so users can
    # set LOCATION_MODE = "" to force city/state/country lookup.
    mode = (LOCATION_MODE or "").strip().upper()
    if mode == "" or mode == "ADDRESS":
        location = get_location_by_address(CITY, STATE, COUNTRY)
    elif mode == "COORDS":
        # allow empty-string LATITUDE/LONGITUDE: if coords lookup fails,
        # fall back to address lookup so users can leave lat/lon as "".
        location = get_location_by_coords(LATITUDE, LONGITUDE)
        if not location:
            location = get_location_by_address(CITY, STATE, COUNTRY)
    elif mode == "AUTO":
        location = get_location_by_ip()
    else:
        # Unrecognized mode: fall back to AUTO (IP-based) lookup
        location = get_location_by_ip()

    if not location:
        print("The cosmos remains veiled. Location could not be determined based on the Sankalpa.")
    else:
        ts = load.timescale()
        eph = None
        
        # --- Updated Ephemeris Loading Logic ---
        # Prioritize using a local de421.bsp file if it exists.
        
        local_bsp_file = 'de421.bsp'
        if os.path.exists(local_bsp_file):
            print("Found local de421.bsp file. Using it for calculations.")
            eph = load(local_bsp_file)
        else:
            print("Local de421.bsp file not found. Attempting to download...")
            try:
                # Preferred: let skyfield manage download
                eph = load('de421.bsp')
            except Exception as e:
                print(f"Skyfield download failed: {e}. Trying manual download.")
                # Try a manual download into a local cache directory so we can load from file.
                cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
                os.makedirs(cache_dir, exist_ok=True)
                local_path = os.path.join(cache_dir, 'de421.bsp')
                url = 'https://ssd.jpl.nasa.gov/ftp/eph/planets/bsp/de421.bsp'
                try:
                    # first try with normal verification
                    r = requests.get(url, timeout=30)
                    r.raise_for_status()
                    with open(local_path, 'wb') as fh: fh.write(r.content)
                except Exception:
                    try:
                        # As a last resort try without SSL verification (not recommended)
                        import urllib3
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        r = requests.get(url, timeout=30, verify=False)
                        r.raise_for_status()
                        with open(local_path, 'wb') as fh: fh.write(r.content)
                    except Exception:
                        print("Warning: could not download ephemeris. Moon information will be skipped.")
                        local_path = None

                if local_path and os.path.exists(local_path):
                    try:
                        eph = load(local_path)
                    except Exception:
                        eph = None
        
        observer = wgs84.latlon(location['latitude'], location['longitude'])
        tz = pytz.timezone(location['timezone']); now = datetime.now(tz)
        t0 = ts.from_datetime(now); t1 = ts.from_datetime(now + timedelta(days=1))
        
        print(f"--- Qibla-Numa Report for: {location['address']} ---")
        
        # We use our own artisan for the Sun's decree.
        sun_times = LocalPrayerCalculator(location['latitude'], location['longitude'], location['timezone'], MADHAB, PRAYER_METHOD_ANGLES['fajr'], PRAYER_METHOD_ANGLES['isha']).calculate_times_for_date(now)
        print("\n☀️ The Sun's Decree (Prayer Times)")
        print(f"   Fajr:    {format_time(sun_times['fajr'])}")
        print(f"   Sunrise: {format_time(sun_times['sunrise'])}")
        print(f"   Dhuhr:   {format_time(sun_times['dhuhr'])}")
        print(f"   Asr:     {format_time(sun_times['asr'])}")
        print(f"   Maghrib: {format_time(sun_times['maghrib'])}")
        print(f"   Isha:    {format_time(sun_times['isha'])}")
        
        # We still ask the Master Artisan Skyfield for the Moon's secrets, as he knows them best.
        if eph is not None:
            moon_times = calculate_moon_mysteries(eph, observer, ts, t0, t1, tz)
            # If ascent/descent at 45° couldn't be found, estimate them as
            # midpoints between rise->transit and transit->set respectively.
            # This is a heuristic estimate and not an astronomical calculation
            # of the actual 45° crossing, but it gives a reasonable placeholder
            # when the Moon never reaches 45° altitude during the day's window.
            try:
                if not moon_times.get('ascent_45'):
                    r = moon_times.get('rise')
                    tr = moon_times.get('transit')
                    if r and tr:
                        moon_times['ascent_45'] = r + (tr - r) / 2
                if not moon_times.get('descent_45'):
                    tr = moon_times.get('transit')
                    s = moon_times.get('set')
                    if tr and s:
                        moon_times['descent_45'] = tr + (s - tr) / 2
            except Exception:
                # keep original None values if any arithmetic fails
                pass
            # compute current moon alt/az/distance and upcoming phases
            t_now = ts.from_datetime(now)
            topo = (eph['earth'] + observer).at(t_now)
            astrometric = topo.observe(eph['moon'])
            apparent = astrometric.apparent()
            alt, az, distance = apparent.altaz()
            
            print("\n🌙 The Moon's Mysteries (Local Time)")
            print(f"   Moonrise:    {format_time(moon_times['rise'])}")
            print(f"   Ascent 45°:  {format_time(moon_times['ascent_45'])}")
            print(f"   Zenith:      {format_time(moon_times['transit'])}")
            print(f"   Descent 45°: {format_time(moon_times['descent_45'])}")
            print(f"   Moonset:     {format_time(moon_times['set'])}")
            # current moon metrics
            def fmt_deg(d):
                try: return f"{d.degrees:.2f}°"
                except Exception: return "n/a"
            def fmt_dist(d):
                try:
                    # convert AU to miles (1 AU = 92,955,807.3 miles approx)
                    return f"{d.au * 92955807.3:,.0f} mi"
                except Exception:
                    return "n/a"

            print("\n   Current Moon:")
            print(f"     Direction (azimuth): {fmt_deg(az)}")
            print(f"     Altitude:            {fmt_deg(alt)}")
            print(f"     Distance:            {fmt_dist(distance)}")
            
            # --- FIX: Find and display upcoming phases in chronological order ---
            phase_f = almanac.moon_phases(eph)
            # Start search from now and look ahead 35 days to find the next of all 4 phases
            phase_t0 = ts.from_datetime(now)
            phase_t1 = ts.from_datetime(now + timedelta(days=35))
            phase_times, phase_vals = almanac.find_discrete(phase_t0, phase_t1, phase_f)

            upcoming_phases = []
            found_phases = set() # To store names of phases we've already found

            for tt, pv in zip(phase_times, phase_vals):
                name = almanac.MOON_PHASES[pv]
                if name not in found_phases:
                    upcoming_phases.append({'name': name, 'date': tt.utc_datetime().astimezone(tz)})
                    found_phases.add(name)
            
            # Sort the found phases by date to ensure chronological order
            upcoming_phases.sort(key=lambda x: x['date'])

            print('\n   Upcoming Primary Phases:')
            if upcoming_phases:
                for phase in upcoming_phases:
                    date_str = phase['date'].strftime('%b %d, %Y, %I:%M %p')
                    print(f"     {phase['name']:<15}: {date_str}")
            else:
                print("     Could not determine upcoming phases.")

        else:
            print("\n🌙 Moon data unavailable (ephemeris load failed).")

        # compute and print subsolar and sublunar city estimates
        try:
            t_now_sf = ts.from_datetime(now)
            sun_lat, sun_lon = subpoint_of_body(eph, 'sun', t_now_sf)
            moon_lat, moon_lon = subpoint_of_body(eph, 'moon', t_now_sf)

            sun_city = None if sun_lat is None else nearest_city_for(sun_lat, sun_lon)
            moon_city = None if moon_lat is None else nearest_city_for(moon_lat, moon_lon)

            def local_time_at(lat, lon):
                try:
                    tf = TimezoneFinder(); tzname = tf.timezone_at(lng=lon, lat=lat)
                    if not tzname: return None, None
                    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
                    lt = now_utc.astimezone(pytz.timezone(tzname))
                    return lt, tzname
                except Exception:
                    return None, None

            sun_local, sun_tz = (None, None) if sun_lat is None else local_time_at(sun_lat, sun_lon)
            moon_local, moon_tz = (None, None) if moon_lat is None else local_time_at(moon_lat, moon_lon)

            print('\nSub-point summary:')
            # Always show lat/lon when available and include nearest city/country if found
            if sun_lat is not None:
                sun_loc_str = f"{sun_lat:.5f}, {sun_lon:.5f}"
                if sun_city:
                    sun_loc_str += f"  — nearest: {sun_city}"
                sun_time_str = sun_local.strftime('%b %d, %Y, %I:%M %p') if sun_local else 'n/a'
                print(f"  Sun zenith (subsolar): {sun_loc_str} (tz: {sun_tz}) local time: {sun_time_str}")
            else:
                print('  Sun zenith: n/a')

            if moon_lat is not None:
                moon_loc_str = f"{moon_lat:.5f}, {moon_lon:.5f}"
                if moon_city:
                    moon_loc_str += f"  — nearest: {moon_city}"
                moon_time_str = moon_local.strftime('%b %d, %Y, %I:%M %p') if moon_local else 'n/a'
                print(f"  Moon zenith (sublunar): {moon_loc_str} (tz: {moon_tz}) local time: {moon_time_str}")
            else:
                print('  Moon zenith: n/a')
        except Exception:
            pass

        print("-" * 45)