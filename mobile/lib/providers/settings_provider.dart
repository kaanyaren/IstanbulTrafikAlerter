import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';

class SettingsState {
  final bool notificationsEnabled;
  final double notificationThreshold;
  final List<String> watchedZones;
  final String themeMode; // 'system', 'light', 'dark'
  final String language; // 'tr', 'en'

  const SettingsState({
    this.notificationsEnabled = true,
    this.notificationThreshold = 70.0,
    this.watchedZones = const [],
    this.themeMode = 'system',
    this.language = 'tr',
  });

  SettingsState copyWith({
    bool? notificationsEnabled,
    double? notificationThreshold,
    List<String>? watchedZones,
    String? themeMode,
    String? language,
  }) {
    return SettingsState(
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      notificationThreshold: notificationThreshold ?? this.notificationThreshold,
      watchedZones: watchedZones ?? this.watchedZones,
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
      notificationThreshold: prefs.getDouble(AppConstants.notifThresholdKey) ?? 70.0,
      watchedZones: prefs.getStringList(AppConstants.watchedZonesKey) ?? [],
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

  Future<void> toggleWatchedZone(String zone) async {
    final prefs = await SharedPreferences.getInstance();
    final currentZones = List<String>.from(state.watchedZones);
    
    if (currentZones.contains(zone)) {
      currentZones.remove(zone);
    } else {
      currentZones.add(zone);
    }
    
    await prefs.setStringList(AppConstants.watchedZonesKey, currentZones);
    state = state.copyWith(watchedZones: currentZones);
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

final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>((ref) {
  return SettingsNotifier();
});
