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
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut

# ==============================================================================
# --- SANKALPA INSCRIPTION (THE SACRED DECREE) ---
# Carve your will here. The script will obey this Hukm (Command) without question.
# ==============================================================================

LOCATION_MODE = "AUTO" 
CITY = "Delhi"
STATE = ""
COUNTRY = "India"
LATITUDE = 28.6139
LONGITUDE = 77.2090
PRAYER_METHOD_ANGLES = {"fajr": 18.0, "isha": 18.0}
MADHAB = "hanafi"

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
        transit_list = [_to_dt(t) for t in times_mer]

        def choose_best(events):
            if not events:
                return None
            for e in events:
                if e >= day_start and e < day_end:
                    return e
            midpoint = day_start + (day_end - day_start) / 2
            return min(events, key=lambda x: abs((x - midpoint).total_seconds()))

        moon_times['rise'] = choose_best(rise_list)
        moon_times['transit'] = choose_best(transit_list)
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
                alt = eph['moon'].at(sf_t).observe(observer).apparent().altaz()[0].degrees
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
        alt = eph['moon'].at(t).observe(observer).apparent().altaz()[0].degrees
        return alt > 45.0

    try:
        times45, events45 = almanac.find_discrete(alt_search_start, alt_search_end, moon_above_45)
        crossings = [_to_dt(t) for t in times45]
        ascent = None; descent = None

        # events45[i] is True if moon_above_45 is True after times45[i]. To detect
        # transitions we compare consecutive event states. An ascent is where
        # events45[i] is True and (i==0 or events45[i-1] is False). A descent is
        # where events45[i] is False and (i==0 or events45[i-1] is True).
        for i, t_obj in enumerate(crossings):
            state = bool(events45[i])
            prev_state = bool(events45[i-1]) if i > 0 else None
            if t_obj >= day_start and t_obj < day_end:
                if state and (prev_state is False or prev_state is None) and ascent is None:
                    ascent = t_obj
                if not state and (prev_state is True or prev_state is None) and descent is None:
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
        sp = eph[body].at(t).subpoint()
        return sp.latitude.degrees, sp.longitude.degrees
    except Exception:
        # fallback: compute geocentric vector and convert to lat/lon via .subpoint on apparent
        try:
            sp = eph['earth'].at(t).observe(eph[body]).apparent().subpoint()
            return sp.latitude.degrees, sp.longitude.degrees
        except Exception:
            return None, None


def nearest_city_for(lat, lon):
    """Use Nominatim reverse geocoding to get a nearby city name; return display string."""
    try:
        geolocator = Nominatim(user_agent="cosmic_compass")
        loc = geolocator.reverse(f"{lat}, {lon}", zoom=10, language='en', timeout=10)
        if not loc:
            return None
        addr = loc.raw.get('address', {})
        for key in ('city', 'town', 'village', 'hamlet', 'county'):
            if addr.get(key):
                return addr.get(key)
        # fallback to display_name
        return loc.raw.get('display_name')
    except (GeocoderUnavailable, GeocoderTimedOut, Exception):
        return None

if __name__ == "__main__":
    location = None
    if LOCATION_MODE == "ADDRESS": location = get_location_by_address(CITY, STATE, COUNTRY)
    elif LOCATION_MODE == "COORDS": location = get_location_by_coords(LATITUDE, LONGITUDE)
    else: location = get_location_by_ip()

    if not location:
        print("The cosmos remains veiled. Location could not be determined based on the Sankalpa.")
    else:
        ts = load.timescale()
        eph = None
        try:
            # Preferred: let skyfield manage download
            eph = load('de421.bsp')
        except Exception:
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
            # get upcoming moon phases (next 30 days)
            phase_f = almanac.moon_phases(eph)
            phase_t0 = ts.from_datetime(now)
            phase_t1 = ts.from_datetime(now + timedelta(days=30))
            phase_times, phase_vals = almanac.find_discrete(phase_t0, phase_t1, phase_f)
            next_new = None; next_full = None
            for tt, pv in zip(phase_times, phase_vals):
                name = almanac.MOON_PHASES[pv]
                if name == 'New Moon' and next_new is None: next_new = tt.utc_datetime().astimezone(tz)
                if name == 'Full Moon' and next_full is None: next_full = tt.utc_datetime().astimezone(tz)
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
            print(f"     Full Moon:           {next_full.strftime('%b %d, %Y, %I:%M %p') if next_full else 'n/a'}")
            print(f"     New Moon:            {next_new.strftime('%b %d, %Y, %I:%M %p') if next_new else 'n/a'}")
            # compute exact phase instants for the upcoming lunation (new, first, full, last)
            phase_f = almanac.moon_phases(eph)
            phase_t0 = ts.from_datetime(now - timedelta(days=1))
            phase_t1 = ts.from_datetime(now + timedelta(days=40))
            phase_times, phase_vals = almanac.find_discrete(phase_t0, phase_t1, phase_f)
            exact_phases = {}
            for tt, pv in zip(phase_times, phase_vals):
                name = almanac.MOON_PHASES[pv]
                if name not in exact_phases:
                    exact_phases[name] = tt.utc_datetime().astimezone(tz)

            # print daily phases for the upcoming lunation starting at next_new
            if next_new:
                phases = daily_moon_phase_names(eph, ts, next_new, tz, days=30)
                # condense to one representative date per canonical phase
                canonical = [
                    'New Moon', 'Waxing Crescent', 'First Quarter', 'Waxing Gibbous',
                    'Full Moon', 'Waning Gibbous', 'Third Quarter', 'Waning Crescent'
                ]
                found = {}
                for d, p in phases:
                    if p in canonical and p not in found:
                        found[p] = d
                        # stop early if we found all
                        if len(found) == len(canonical):
                            break

                print('\nUpcoming Lunation:')
                for p in canonical:
                    # compute representative exact instants for waxing/waning thresholds
                    # thresholds: 25% and 75% illumination
                    def find_threshold_crossings(threshold, start_dt, end_dt):
                        t0 = ts.from_datetime(start_dt - timedelta(days=1))
                        t1 = ts.from_datetime(end_dt + timedelta(days=1))
                        def above(t):
                            return almanac.fraction_illuminated(eph, 'moon', t) > threshold
                        times_t, events_t = almanac.find_discrete(t0, t1, above)
                        return [tt.utc_datetime().astimezone(tz) for tt in times_t], events_t

                    # Determine window boundaries
                    new_dt = exact_phases.get('New Moon')
                    fq_dt = exact_phases.get('First Quarter')
                    full_dt = exact_phases.get('Full Moon')
                    lq_dt = exact_phases.get('Last Quarter')
                    # try to determine next new after lq if available in exact_phases list
                    next_new_dt = None
                    if new_dt:
                        # if there are multiple new instants we might have the next one in exact_phases; otherwise estimate
                        # find any phase_times labeled 'New Moon' after new_dt
                        new_candidates = [tt.utc_datetime().astimezone(tz) for tt,pv in zip(phase_times, phase_vals) if almanac.MOON_PHASES[pv]=='New Moon' and tt.utc_datetime().astimezone(tz) > new_dt]
                        if new_candidates:
                            next_new_dt = new_candidates[0]

                    # find 25% crossings
                    crossings25, events25 = [], []
                    try:
                        crossings25, events25 = find_threshold_crossings(0.25, new_dt or now, next_new_dt or (new_dt + timedelta(days=30) if new_dt else now + timedelta(days=30)))
                    except Exception:
                        pass
                    crossings75, events75 = [], []
                    try:
                        crossings75, events75 = find_threshold_crossings(0.75, new_dt or now, next_new_dt or (new_dt + timedelta(days=30) if new_dt else now + timedelta(days=30)))
                    except Exception:
                        pass

                    # helper to pick crossing inside an interval
                    def pick_between(crossings, start, end):
                        for c in crossings:
                            if start and end and c >= start and c <= end:
                                return c
                        return None

                    if p == 'Full Moon':
                        print(f"  {p}: {exact_phases.get('Full Moon').strftime('%b %d, %Y, %I:%M %p') if exact_phases.get('Full Moon') else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    elif p == 'New Moon':
                        print(f"  {p}: {exact_phases.get('New Moon').strftime('%b %d, %Y, %I:%M %p') if exact_phases.get('New Moon') else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    elif p == 'First Quarter':
                        print(f"  {p}: {exact_phases.get('First Quarter').strftime('%b %d, %Y, %I:%M %p') if exact_phases.get('First Quarter') else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    elif p == 'Third Quarter' or p == 'Last Quarter':
                        print(f"  Third Quarter: {exact_phases.get('Last Quarter').strftime('%b %d, %Y, %I:%M %p') if exact_phases.get('Last Quarter') else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    elif p == 'Waxing Crescent':
                        # 25% crossing between New and First Quarter
                        val = pick_between(crossings25, new_dt, fq_dt)
                        print(f"  {p}: {val.strftime('%b %d, %Y, %I:%M %p') if val else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    elif p == 'Waxing Gibbous':
                        # 75% crossing between First Quarter and Full
                        val = pick_between(crossings75, fq_dt, full_dt)
                        print(f"  {p}: {val.strftime('%b %d, %Y, %I:%M %p') if val else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    elif p == 'Waning Gibbous':
                        # 75% crossing between Full and Last Quarter
                        val = pick_between(crossings75, full_dt, lq_dt)
                        print(f"  {p}: {val.strftime('%b %d, %Y, %I:%M %p') if val else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    elif p == 'Waning Crescent':
                        # 25% crossing between Last Quarter and next New
                        val = pick_between(crossings25, lq_dt, next_new_dt)
                        print(f"  {p}: {val.strftime('%b %d, %Y, %I:%M %p') if val else (found.get(p).isoformat() if found.get(p) else 'n/a')}")
                    else:
                        print(f"  {p}: {found.get(p).isoformat() if found.get(p) else 'n/a'}")
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
            if sun_lat is not None:
                print(f"  Sun zenith (subsolar) at: {sun_city or f'{sun_lat:.3f},{sun_lon:.3f}'} (tz: {sun_tz}) local time: {sun_local.strftime('%b %d, %Y, %I:%M %p') if sun_local else 'n/a'}")
            else:
                print('  Sun zenith: n/a')
            if moon_lat is not None:
                print(f"  Moon zenith (sublunar) at: {moon_city or f'{moon_lat:.3f},{moon_lon:.3f}'} (tz: {moon_tz}) local time: {moon_local.strftime('%b %d, %Y, %I:%M %p') if moon_local else 'n/a'}")
            else:
                print('  Moon zenith: n/a')
        except Exception:
            pass

        print("-" * 45)