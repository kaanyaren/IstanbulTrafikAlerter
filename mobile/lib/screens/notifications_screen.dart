import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/settings_provider.dart';
import '../providers/map_provider.dart';
import '../services/notification_service.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final predictions = ref.watch(predictionsCacheProvider);
    final top = [...predictions]..sort((a, b) => b.score.compareTo(a.score));
    final critical = top.take(5).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Trafik Uyarıları'),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: NotificationService.showTestNotification,
        icon: const Icon(Icons.send),
        label: const Text('Test'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
        children: [
          Card(
            child: SwitchListTile(
              title: const Text('Canlı trafik bildirimleri'),
              subtitle:
                  const Text('Yoğunluk eşiğini aşan bölgelerde push gönder'),
              value: settings.notificationsEnabled,
              onChanged: (v) async {
                if (v) {
                  final granted = await NotificationService.requestPermission();
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
                    .updateNotificationsEnabled(v);
              },
            ),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Uyarı Eşiği',
                    style: TextStyle(fontWeight: FontWeight.w700),
                  ),
                  Slider(
                    value: settings.notificationThreshold,
                    min: 50,
                    max: 100,
                    divisions: 10,
                    label: settings.notificationThreshold.round().toString(),
                    onChanged: (v) => ref
                        .read(settingsProvider.notifier)
                        .updateNotificationThreshold(v),
                  ),
                  Text(
                      'Anlık eşik: ${settings.notificationThreshold.toInt()}+'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          Text(
            'Canlı Risk Alanları',
            style: Theme.of(context)
                .textTheme
                .titleLarge
                ?.copyWith(fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 10),
          if (critical.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text('Henüz kritik yoğunluk verisi yok.'),
              ),
            ),
          ...critical.map(
            (p) => Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: ListTile(
                leading: const Icon(Icons.warning_amber_rounded,
                    color: Colors.orange),
                title: Text(p.zoneName ?? 'Bilinmeyen Bölge'),
                subtitle: Text('Skor: ${p.score}% • ${p.label}'),
                trailing: const Icon(Icons.chevron_right),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
