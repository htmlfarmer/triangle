<?php
// Simple, minimal PHP wrapper to run the existing Python script and show its output.
// Location: /home/asher/public_html/try.php
// Usage examples:
//  /try.php?mode=AUTO
//  /try.php?city=Moscow&country=Russia&mode=ADDRESS
//  /try.php?lat=55.7558&lon=37.6176&mode=COORDS
//  Optional: &fajr=18.0&isha=18.0&madhab=hanafi
//
// Security notes:
//  - Script path and python binary are fixed below (no user-controlled exec).
//  - Inputs are validated and escaped before being placed into environment variables.
//  - A system timeout is used to avoid long-running processes.

$SCRIPT_PATH = '/home/asher/github/triangle/try.py';
$PYTHON = '/usr/bin/python3'; // adjust if python3 is elsewhere
$TIMEOUT_SECONDS = 30;

// allowed simple values
$allowed_modes = ['AUTO', 'ADDRESS', 'COORDS', ''];
$allowed_madhab = ['hanafi', 'shafi', '']; // adjust if you support more

// collect and sanitize inputs
$get = function($k){
    return isset($_GET[$k]) ? trim($_GET[$k]) : '';
};
$mode = strtoupper($get('mode'));
$mode = in_array($mode, $allowed_modes, true) ? $mode : '';
$city = substr($get('city'), 0, 200);
$state = substr($get('state'), 0, 200);
$country = substr($get('country'), 0, 200);
$lat = $get('lat'); $lon = $get('lon');
$fajr = $get('fajr'); $isha = $get('isha');
$madhab = strtolower($get('madhab'));
$madhab = in_array($madhab, $allowed_madhab, true) ? $madhab : '';

// numeric validation
if ($lat !== '' && !is_numeric($lat)) $lat = '';
if ($lon !== '' && !is_numeric($lon)) $lon = '';
if ($fajr !== '' && !is_numeric($fajr)) $fajr = '';
if ($isha !== '' && !is_numeric($isha)) $isha = '';

// --- new: attempt to detect client IP and lookup lat/lon if not provided ---
function get_client_ip() {
    // prefer X-Forwarded-For (first entry), then Client-IP, then REMOTE_ADDR
    if (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $parts = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
        $ip = trim($parts[0]);
        if ($ip) return $ip;
    }
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        return trim($_SERVER['HTTP_CLIENT_IP']);
    }
    return isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '';
}

function is_private_ip($ip) {
    if (!filter_var($ip, FILTER_VALIDATE_IP)) return true;
    // IPv4 private ranges
    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) {
        $long = ip2long($ip);
        $private_ranges = [
            ['start' => ip2long('10.0.0.0'),      'end' => ip2long('10.255.255.255')],
            ['start' => ip2long('172.16.0.0'),    'end' => ip2long('172.31.255.255')],
            ['start' => ip2long('192.168.0.0'),   'end' => ip2long('192.168.255.255')],
            ['start' => ip2long('127.0.0.0'),     'end' => ip2long('127.255.255.255')],
        ];
        foreach ($private_ranges as $r) {
            if ($long >= $r['start'] && $long <= $r['end']) return true;
        }
        return false;
    }
    // IPv6 loopback or unique local address (fc00::/7)
    if (strpos($ip, '::1') !== false) return true;
    if (stripos($ip, 'fc') === 0 || stripos($ip, 'fd') === 0) return true;
    return false;
}

$detected_ip = get_client_ip();
$geo_lookup_note = '';
// Only attempt lookup if user did not supply lat/lon and IP appears public
if (($lat === '' || $lon === '') && $detected_ip !== '' && !is_private_ip($detected_ip)) {
    // use ip-api.com simple JSON endpoint with a short timeout
    $url = 'http://ip-api.com/json/' . rawurlencode($detected_ip) . '?fields=status,message,lat,lon,query';
    $ctx = stream_context_create(['http' => ['timeout' => 2]]); // 2s timeout
    $json = @file_get_contents($url, false, $ctx);
    if ($json !== false) {
        $data = json_decode($json, true);
        if (is_array($data) && isset($data['status']) && $data['status'] === 'success') {
            if ($lat === '' && isset($data['lat'])) $lat = $data['lat'];
            if ($lon === '' && isset($data['lon'])) $lon = $data['lon'];
            $geo_lookup_note = 'GeoIP lookup succeeded for ' . ($data['query'] ?? $detected_ip);
        } else {
            $geo_lookup_note = 'GeoIP lookup failed: ' . ($data['message'] ?? 'unknown');
        }
    } else {
        $geo_lookup_note = 'GeoIP lookup request failed or timed out';
    }
} elseif ($detected_ip !== '' && is_private_ip($detected_ip)) {
    $geo_lookup_note = 'Client IP is private/local, skipping GeoIP lookup';
} else {
    // nothing to do or lat/lon already provided
}

// ensure script exists and is readable
if (!is_file($SCRIPT_PATH) || !is_readable($SCRIPT_PATH)) {
    http_response_code(500);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Error: Python script not found or not readable at {$SCRIPT_PATH}\n";
    exit;
}

// build environment variables (only the keys the Python script expects)
$env = [];
if ($mode !== '')    $env['LOCATION_MODE'] = $mode;
if ($city !== '')    $env['CITY'] = $city;
if ($state !== '')   $env['STATE'] = $state;
if ($country !== '') $env['COUNTRY'] = $country;
if ($lat !== '')     $env['LATITUDE'] = $lat;
if ($lon !== '')     $env['LONGITUDE'] = $lon;
if ($fajr !== '')    $env['PRAYER_METHOD_ANGLES_FAJR'] = $fajr; // optional mapping
if ($isha !== '')    $env['PRAYER_METHOD_ANGLES_ISHA'] = $isha;
if ($madhab !== '')  $env['MADHAB'] = $madhab;
// include debug info about detected IP / geo lookup
if ($detected_ip !== '') $env['GEOIP_DETECTED_IP'] = $detected_ip;
if ($geo_lookup_note !== '') $env['GEOIP_NOTE'] = $geo_lookup_note;

// map simple env keys to ones used by try.py (try.py expects PRAYER_METHOD_ANGLES dict; we provide numeric env fallbacks)
$env_parts = [];
foreach ($env as $k => $v) {
    // permit only A-Z0-9_ in env names
    $k_safe = preg_replace('/[^A-Z0-9_]/', '', strtoupper($k));
    $env_parts[] = $k_safe . '=' . escapeshellarg($v);
}
$env_str = implode(' ', $env_parts);

// build command safely
$python_cmd = escapeshellcmd($PYTHON);
$script_arg = escapeshellarg($SCRIPT_PATH);
$timeout_cmd = 'timeout ' . intval($TIMEOUT_SECONDS) . 's'; // requires coreutils timeout on the server

$full_cmd = trim($env_str . ' ' . $timeout_cmd . ' ' . $python_cmd . ' ' . $script_arg . ' 2>&1');

// run command and capture output
// shell_exec is simple; we already prevented user-controlled execables/paths in $PYTHON and $SCRIPT_PATH
$output = shell_exec($full_cmd);
if ($output === null) $output = "Error: command failed or timed out.";

// return a minimal HTML page with preformatted output
header('Content-Type: text/html; charset=utf-8');
?>
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>try.py output</title>
  <style>body{font-family:system-ui,Segoe UI,Arial;margin:20px}pre{background:#f5f5f5;padding:12px;border-radius:6px;overflow:auto}</style>
</head>
<body>
  <h3>try.py output</h3>
  <p><strong>Command run (for debugging):</strong></p>
  <pre><?php echo htmlspecialchars($full_cmd, ENT_QUOTES|ENT_SUBSTITUTE, 'UTF-8'); ?></pre>
  <p><strong>Script output:</strong></p>
  <pre><?php echo htmlspecialchars($output, ENT_QUOTES|ENT_SUBSTITUTE, 'UTF-8'); ?></pre>
  <?php if ($detected_ip !== ''): ?>
    <p><strong>Detected client IP:</strong> <?php echo htmlspecialchars($detected_ip, ENT_QUOTES|ENT_SUBSTITUTE, 'UTF-8'); ?></p>
  <?php endif; ?>
  <?php if ($geo_lookup_note !== ''): ?>
    <p><strong>GeoIP note:</strong> <?php echo htmlspecialchars($geo_lookup_note, ENT_QUOTES|ENT_SUBSTITUTE, 'UTF-8'); ?></p>
  <?php endif; ?>
  <hr>
  <p>Usage: append query params like ?mode=AUTO or ?city=Moscow&country=Russia or ?lat=55.7558&lon=37.6176</p>
</body>
</html>