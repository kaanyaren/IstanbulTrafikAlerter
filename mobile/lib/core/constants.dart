import 'package:flutter/foundation.dart';

class AppConstants {
  // API
  static String get baseUrl => kIsWeb ? 'http://localhost:8000' : 'http://10.0.2.2:8000';
  static const Duration connectTimeout = Duration(seconds: 10);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const int maxRetries = 3;

  // Map Tile Providers (CartoDB - free, no API key)
  static const String cartoDarkUrl = 'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  static const String cartoLightUrl = 'https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';
  static const String cartoAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

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
