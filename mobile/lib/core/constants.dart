class AppConstants {
  // ── Supabase ────────────────────────────────────────────────────────────
  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://iksvpfaezyxjhpfbuwqn.supabase.co',
  );
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue:
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlrc3ZwZmFlenl4amhwZmJ1d3FuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIyMDg0NjgsImV4cCI6MjA4Nzc4NDQ2OH0.-FDbjfcJ0pdbeOOXqRbaAEyvyOnpwuV8L7TA01xbyTQ',
  );

  // ── Legacy API (kept for reference, no longer used) ─────────────────────
  static String get baseUrl => supabaseUrl;
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const int maxRetries = 3;

  // Map Tile Providers (CartoDB - free, no API key)
  static const String cartoDarkUrl =
      'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  static const String cartoLightUrl =
      'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
  static const String cartoAttribution =
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

  // HERE Traffic Flow Tile (transparent overlay)
  // Traffic Raster Tile v3 — canlı trafik akışı çizgilerini saydam PNG olarak verir
  static String hereTrafficFlowUrl(String apiKey) =>
      'https://traffic.maps.hereapi.com/v3/flow/mc/{z}/{x}/{y}/png8?apikey=$apiKey';
  static const String hereAttribution =
      '&copy; <a href="https://legal.here.com/terms">HERE</a>';

  // Istanbul center coordinates
  static const double istanbulLat = 41.0082;
  static const double istanbulLon = 28.9784;
  static const double defaultZoom = 12.0;
  static const double defaultRadiusKm = 10.0;

  // Notifications
  static const String notifChannelId = 'traffic_alerts';
  static const String notifChannelName = 'Trafik Uyarıları';
  static const String notifChannelDesc = 'Yoğun trafik bölgeleri için uyarılar';

  // StorageKeys
  static const String tokenKey = 'auth_token';
  static const String notifEnabledKey = 'notif_enabled';
  static const String notifThresholdKey = 'notif_threshold';
  static const String themeModeKey = 'theme_mode';
  static const String languageKey = 'language';
}
