import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';

class SettingsState {
  final bool notificationsEnabled;
  final double notificationThreshold;
  final String themeMode; // 'system', 'light', 'dark'
  final String language; // 'tr', 'en'

  const SettingsState({
    this.notificationsEnabled = true,
    this.notificationThreshold = 70.0,
    this.themeMode = 'system',
    this.language = 'tr',
  });

  SettingsState copyWith({
    bool? notificationsEnabled,
    double? notificationThreshold,
    String? themeMode,
    String? language,
  }) {
    return SettingsState(
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      notificationThreshold:
          notificationThreshold ?? this.notificationThreshold,
      themeMode: themeMode ?? this.themeMode,
      language: language ?? this.language,
    );
  }
}

class SettingsNotifier extends StateNotifier<SettingsState> {
  SettingsNotifier() : super(const SettingsState()) {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();

    state = SettingsState(
      notificationsEnabled: prefs.getBool(AppConstants.notifEnabledKey) ?? true,
      notificationThreshold:
          prefs.getDouble(AppConstants.notifThresholdKey) ?? 70.0,
      themeMode: prefs.getString(AppConstants.themeModeKey) ?? 'system',
      language: prefs.getString(AppConstants.languageKey) ?? 'tr',
    );
  }

  Future<void> updateNotificationsEnabled(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(AppConstants.notifEnabledKey, value);
    state = state.copyWith(notificationsEnabled: value);
  }

  Future<void> updateNotificationThreshold(double value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(AppConstants.notifThresholdKey, value);
    state = state.copyWith(notificationThreshold: value);
  }

  Future<void> updateThemeMode(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.themeModeKey, value);
    state = state.copyWith(themeMode: value);
  }

  Future<void> updateLanguage(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(AppConstants.languageKey, value);
    state = state.copyWith(language: value);
  }
}

final settingsProvider =
    StateNotifierProvider<SettingsNotifier, SettingsState>((ref) {
  return SettingsNotifier();
});

// HERE Traffic layer toggle (persisted)
final trafficLayerProvider =
    StateNotifierProvider<TrafficLayerNotifier, bool>((ref) {
  return TrafficLayerNotifier();
});

class TrafficLayerNotifier extends StateNotifier<bool> {
  TrafficLayerNotifier() : super(true) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getBool('traffic_layer_enabled') ?? true;
  }

  Future<void> toggle() async {
    state = !state;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('traffic_layer_enabled', state);
  }
}
