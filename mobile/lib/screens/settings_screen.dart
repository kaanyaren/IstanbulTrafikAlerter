import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/settings_provider.dart';
import '../services/notification_service.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settingsState = ref.watch(settingsProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final surface = isDark ? const Color(0xFF152238) : Colors.white;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ayarlar'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 28),
        children: [
          _sectionTitle(context, 'Bildirim Merkezi'),
          Card(
            color: surface,
            child: Column(
              children: [
                SwitchListTile(
                  title: const Text('Trafik Uyarı Bildirimleri'),
                  subtitle:
                      const Text('Önemli trafik artışlarında bildirim alın'),
                  value: settingsState.notificationsEnabled,
                  onChanged: (val) async {
                    if (val) {
                      final granted =
                          await NotificationService.requestPermission();
                      if (!granted && context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              'Bildirim izni verilmedi. Ayarlardan izin vererek tekrar deneyin.',
                            ),
                          ),
                        );
                        await ref
                            .read(settingsProvider.notifier)
                            .updateNotificationsEnabled(false);
                        return;
                      }
                    }
                    await ref
                        .read(settingsProvider.notifier)
                        .updateNotificationsEnabled(val);
                  },
                  activeThumbColor: theme.primaryColor,
                ),
                ListTile(
                  title: Text(
                      'Eşik: ${settingsState.notificationThreshold.toInt()}+'),
                  subtitle: Slider(
                    value: settingsState.notificationThreshold,
                    min: 50,
                    max: 100,
                    divisions: 10,
                    label:
                        settingsState.notificationThreshold.round().toString(),
                    onChanged: (val) {
                      ref
                          .read(settingsProvider.notifier)
                          .updateNotificationThreshold(val);
                    },
                  ),
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(0, 0, 16, 12),
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.send),
                      label: const Text('Test Bildirimi Gönder'),
                      onPressed: NotificationService.showTestNotification,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          _sectionTitle(context, 'Görünüm ve Dil'),
          Card(
            color: surface,
            child: Column(
              children: [
                ListTile(
                  title: const Text('Tema'),
                  trailing: DropdownButton<String>(
                    value: settingsState.themeMode,
                    underline: const SizedBox(),
                    items: const [
                      DropdownMenuItem(value: 'system', child: Text('Sistem')),
                      DropdownMenuItem(value: 'light', child: Text('Açık')),
                      DropdownMenuItem(value: 'dark', child: Text('Koyu')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        ref
                            .read(settingsProvider.notifier)
                            .updateThemeMode(val);
                      }
                    },
                  ),
                ),
                ListTile(
                  title: const Text('Dil'),
                  trailing: DropdownButton<String>(
                    value: settingsState.language,
                    underline: const SizedBox(),
                    items: const [
                      DropdownMenuItem(value: 'tr', child: Text('Türkçe')),
                      DropdownMenuItem(value: 'en', child: Text('English')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        ref.read(settingsProvider.notifier).updateLanguage(val);
                      }
                    },
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Center(
            child: Text(
              'Versiyon 1.0.0',
              style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _sectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
            ),
      ),
    );
  }
}
