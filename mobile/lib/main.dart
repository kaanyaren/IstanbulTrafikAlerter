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
  String? startupError;

  if (AppConstants.supabaseUrl.isEmpty ||
      AppConstants.supabaseAnonKey.isEmpty) {
    startupError =
        'Supabase ayarlari bulunamadi. Uygulamayi --dart-define ile SUPABASE_URL ve SUPABASE_ANON_KEY vererek baslatin.';
  }

  if (startupError == null) {
    try {
      // Supabase baglantisini baslat; sure asimi olursa splash'ta takilmayalim.
      await Supabase.initialize(
        url: AppConstants.supabaseUrl,
        anonKey: AppConstants.supabaseAnonKey,
        realtimeClientOptions: const RealtimeClientOptions(
          eventsPerSecond: 2,
        ),
      ).timeout(const Duration(seconds: 12));

      // Bildirim servisini baslat.
      await NotificationService.initialize()
          .timeout(const Duration(seconds: 6));
    } catch (e) {
      startupError = 'Baslangic sirasinda hata olustu: $e';
    }
  }

  runApp(
    ProviderScope(
      child: IstanbulTrafficAlerterApp(startupError: startupError),
    ),
  );
}

class IstanbulTrafficAlerterApp extends ConsumerWidget {
  const IstanbulTrafficAlerterApp({super.key, this.startupError});

  final String? startupError;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (startupError != null) {
      return MaterialApp(
        title: 'Istanbul Trafik Alerter',
        debugShowCheckedModeBanner: false,
        home: Scaffold(
          appBar: AppBar(title: const Text('Baslangic Hatasi')),
          body: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Uygulama baslatilamadi.',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                Text(startupError!),
              ],
            ),
          ),
        ),
      );
    }

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
