class AppConstants {
  // API
  static const String baseUrl = 'http://10.0.2.2:8000'; // Android emülatör için localhost
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const int maxRetries = 3;

  // Google Maps
  // TODO: Replace with your actual Google Maps API Key
  static const String googleMapsApiKey = 'YOUR_GOOGLE_MAPS_API_KEY';

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
  static const String watchedZonesKey = 'watched_zones';
  static const String themeModeKey = 'theme_mode';
  static const String languageKey = 'language';

  // Districts of Istanbul for zone selection
  static const List<String> istanbulDistricts = [
    'Kadıköy',
    'Beşiktaş',
    'Şişli',
    'Fatih',
    'Beyoğlu',
    'Üsküdar',
    'Maltepe',
    'Ataşehir',
    'Bağcılar',
    'Bakırköy',
    'Başakşehir',
    'Kartal',
  ];
}
