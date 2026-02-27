import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'core/constants.dart';
import 'core/theme.dart';
import 'core/router.dart';
import 'services/notification_service.dart';
import 'providers/settings_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Supabase bağlantısını başlat
  await Supabase.initialize(
    url: AppConstants.supabaseUrl,
    anonKey: AppConstants.supabaseAnonKey,
    realtimeClientOptions: const RealtimeClientOptions(
      eventsPerSecond: 2,
    ),
  );

  // Bildirim servisini başlat
  await NotificationService.initialize();

  runApp(
    const ProviderScope(
      child: IstanbulTrafficAlerterApp(),
    ),
  );
}

class IstanbulTrafficAlerterApp extends ConsumerWidget {
  const IstanbulTrafficAlerterApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // ignore: unused_local_variable
    final settingsState = ref.watch(settingsProvider);

    ThemeMode getThemeMode() {
      switch (settingsState.themeMode) {
        case 'light':
          return ThemeMode.light;
        case 'dark':
          return ThemeMode.dark;
        default:
          return ThemeMode.system;
      }
    }

    return MaterialApp.router(
      title: 'İstanbul Trafik Alerter',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: getThemeMode(),
      routerConfig: appRouter,
    );
  }
}
