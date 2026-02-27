import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../core/constants.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notificationsPlugin = FlutterLocalNotificationsPlugin();

  static Future<void> initialize() async {
    // flutter_local_notifications doesn't support web — skip on web
    if (kIsWeb) {
      debugPrint('[NotificationService] Web platform detected, skipping init.');
      return;
    }

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    
    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _notificationsPlugin.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (response) {
        // Handle notification tap
      },
    );

    // Create channel for Android
    await _createNotificationChannel();
  }

  static Future<void> _createNotificationChannel() async {
    if (kIsWeb) return;

    const channel = AndroidNotificationChannel(
      AppConstants.notifChannelId,
      AppConstants.notifChannelName,
      description: AppConstants.notifChannelDesc,
      importance: Importance.high,
    );

    await _notificationsPlugin
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  static Future<void> showTrafficAlert(String zone, int score, String time) async {
    if (kIsWeb) {
      debugPrint('[NotificationService] Web: $zone - Score: $score at $time');
      return;
    }

    const androidDetails = AndroidNotificationDetails(
      AppConstants.notifChannelId,
      AppConstants.notifChannelName,
      channelDescription: AppConstants.notifChannelDesc,
      importance: Importance.high,
      priority: Priority.high,
      styleInformation: BigTextStyleInformation(''),
    );
    
    const iosDetails = DarwinNotificationDetails();
    
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _notificationsPlugin.show(
      DateTime.now().millisecond, // unique ID
      '⚠️ Yüksek Trafik Uyarı: $zone',
      '$zone bölgesinde $time itibarıyla yüksek trafik bekleniyor (Skor: $score/100).',
      details,
    );
  }

  // Debug için test bildirimi
  static Future<void> showTestNotification() async {
    await showTrafficAlert('Kadıköy', 85, '18:00');
  }
}
