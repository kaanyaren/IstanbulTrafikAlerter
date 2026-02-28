import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../core/constants.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notificationsPlugin =
      FlutterLocalNotificationsPlugin();

  static Future<void> initialize() async {
    // flutter_local_notifications doesn't support web — skip on web
    if (kIsWeb) {
      debugPrint('[NotificationService] Web platform detected, skipping init.');
      return;
    }

    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
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

    // Ask permission once app initializes so the system prompt is shown to user.
    await requestPermission();
  }

  static Future<bool> requestPermission() async {
    if (kIsWeb) return false;

    final androidPlugin =
        _notificationsPlugin.resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    final iosPlugin =
        _notificationsPlugin.resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin>();
    final macPlugin =
        _notificationsPlugin.resolvePlatformSpecificImplementation<
            MacOSFlutterLocalNotificationsPlugin>();

    final androidGranted =
        await androidPlugin?.requestNotificationsPermission() ?? true;
    final iosGranted = await iosPlugin?.requestPermissions(
          alert: true,
          badge: true,
          sound: true,
        ) ??
        true;
    final macGranted = await macPlugin?.requestPermissions(
          alert: true,
          badge: true,
          sound: true,
        ) ??
        true;

    return androidGranted && iosGranted && macGranted;
  }

  static Future<bool> areNotificationsEnabled() async {
    if (kIsWeb) return false;
    final androidPlugin =
        _notificationsPlugin.resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();
    return await androidPlugin?.areNotificationsEnabled() ?? true;
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
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  static Future<void> showTrafficAlert(
      String zone, int score, String time) async {
    if (kIsWeb) {
      debugPrint('[NotificationService] Web: $zone - Score: $score at $time');
      return;
    }

    final enabled = await areNotificationsEnabled();
    if (!enabled) {
      debugPrint('[NotificationService] Notifications are disabled by user.');
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
