import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/settings_provider.dart';
import '../core/constants.dart';
import '../services/notification_service.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settingsState = ref.watch(settingsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Ayarlar'),
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 16),
        children: [
          // Bildirimler Bölümü
          _buildSectionHeader(context, 'Bildirim Tercihleri', Icons.notifications),
          SwitchListTile(
            title: const Text('Trafik Uyarı Bildirimleri'),
            subtitle: const Text('Önemli trafik artışlarında bildirim alın'),
            value: settingsState.notificationsEnabled,
            onChanged: (val) {
              ref.read(settingsProvider.notifier).updateNotificationsEnabled(val);
              if (val) {
                NotificationService.initialize();
              }
            },
            activeColor: theme.primaryColor,
          ),
          
          if (settingsState.notificationsEnabled) 
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Uyarı Eşik Değeri (Trafik Skoru)',
                        style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w500),
                      ),
                      Text(
                        '${settingsState.notificationThreshold.toInt()}+',
                        style: theme.textTheme.bodyLarge?.copyWith(
                          color: theme.primaryColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Slider(
                    value: settingsState.notificationThreshold,
                    min: 50,
                    max: 100,
                    divisions: 10,
                    label: settingsState.notificationThreshold.round().toString(),
                    onChanged: (val) {
                      ref.read(settingsProvider.notifier).updateNotificationThreshold(val);
                    },
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Orta', style: TextStyle(color: Colors.grey, fontSize: 12)),
                        Text('Yüksek', style: TextStyle(color: Colors.grey, fontSize: 12)),
                        Text('Kritik', style: TextStyle(color: Colors.grey, fontSize: 12)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Center(
                    child: OutlinedButton.icon(
                      onIcon: const Icon(Icons.send),
                      icon: const Icon(Icons.send),
                      label: const Text('Test Bildirimi Gönder'),
                      onPressed: () {
                        NotificationService.showTestNotification();
                      },
                    ),
                  ),
                ],
              ),
            ),

          const Divider(height: 32),

          // Bölgeler Bölümü
          _buildSectionHeader(context, 'Takip Edilen Bölgeler', Icons.location_city),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Wrap(
              spacing: 8.0,
              runSpacing: 8.0,
              children: AppConstants.istanbulDistricts.map((district) {
                final isSelected = settingsState.watchedZones.contains(district);
                return FilterChip(
                  label: Text(district),
                  selected: isSelected,
                  onSelected: (_) {
                    ref.read(settingsProvider.notifier).toggleWatchedZone(district);
                  },
                  selectedColor: theme.primaryColor.withOpacity(0.2),
                  checkmarkColor: theme.primaryColor,
                );
              }).toList(),
            ),
          ),

          const Divider(height: 32),

          // Uygulama Görünümü Bölümü
          _buildSectionHeader(context, 'Görünüm', Icons.color_lens),
          ListTile(
            title: const Text('Tema'),
            trailing: DropdownButton<String>(
              value: settingsState.themeMode,
              underline: const SizedBox(),
              items: const [
                DropdownMenuItem(value: 'system', child: Text('Sistem Teması')),
                DropdownMenuItem(value: 'light', child: Text('Açık Tema')),
                DropdownMenuItem(value: 'dark', child: Text('Koyu Tema')),
              ],
              onChanged: (val) {
                if (val != null) {
                  ref.read(settingsProvider.notifier).updateThemeMode(val);
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
          
          const SizedBox(height: 32),
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

  Widget _buildSectionHeader(BuildContext context, String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: Theme.of(context).primaryColor, size: 20),
          const SizedBox(width: 12),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).primaryColor,
            ),
          ),
        ],
      ),
    );
  }
}
