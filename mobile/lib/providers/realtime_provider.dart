import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/prediction.dart';
import '../services/supabase_service.dart';

/// Supabase Realtime ile predictions tablosundaki değişiklikleri dinler.
/// Yeni bir prediction INSERT edildiğinde haritayı otomatik günceller.
class RealtimePredictionsNotifier extends StateNotifier<List<Prediction>> {
  RealtimeChannel? _channel;

  RealtimePredictionsNotifier() : super([]) {
    _subscribe();
  }

  void _subscribe() {
    final client = Supabase.instance.client;

    _channel = client
        .channel('public:predictions')
        .onPostgresChanges(
          event: PostgresChangeEvent.insert,
          schema: 'public',
          table: 'predictions',
          callback: (payload) {
            debugPrint('[Realtime] New prediction: ${payload.newRecord}');
            _onNewPrediction(payload.newRecord);
          },
        )
        .subscribe();

    debugPrint('[Realtime] Subscribed to predictions channel');
  }

  void _onNewPrediction(Map<String, dynamic> record) {
    try {
      final pred = Prediction(
        zoneId: record['zone_id']?.hashCode ?? 0,
        lat: 0, // Will be resolved on next full fetch
        lon: 0,
        score: (record['congestion_score'] as num?)?.toInt() ?? 0,
        timestamp:
            DateTime.tryParse(record['target_time'] ?? '') ?? DateTime.now(),
        label: SupabaseService.scoreToLabel(
            (record['congestion_score'] as num?)?.toInt() ?? 0),
        zoneName: null,
      );

      // Update state: replace existing zone prediction or add new
      final updated = [...state];
      final idx = updated.indexWhere((p) => p.zoneId == pred.zoneId);
      if (idx >= 0) {
        updated[idx] = pred;
      } else {
        updated.add(pred);
      }
      state = updated;
    } catch (e) {
      debugPrint('[Realtime] Error parsing prediction: $e');
    }
  }

  @override
  void dispose() {
    _channel?.unsubscribe();
    super.dispose();
  }
}

/// Provider for real-time prediction updates.
final realtimePredictionsProvider =
    StateNotifierProvider<RealtimePredictionsNotifier, List<Prediction>>(
  (ref) => RealtimePredictionsNotifier(),
);

/// Supabase Realtime ile events tablosundaki değişiklikleri dinler.
class RealtimeEventsNotifier extends StateNotifier<int> {
  RealtimeChannel? _channel;

  /// State is a simple counter that increments on each new event,
  /// triggering a refetch in the UI.
  RealtimeEventsNotifier() : super(0) {
    _subscribe();
  }

  void _subscribe() {
    final client = Supabase.instance.client;

    _channel = client
        .channel('public:events')
        .onPostgresChanges(
          event: PostgresChangeEvent.insert,
          schema: 'public',
          table: 'events',
          callback: (payload) {
            debugPrint('[Realtime] New event: ${payload.newRecord['name']}');
            state = state + 1; // Trigger refetch
          },
        )
        .subscribe();
  }

  @override
  void dispose() {
    _channel?.unsubscribe();
    super.dispose();
  }
}

/// Provider that signals new events have been inserted.
final realtimeEventsProvider =
    StateNotifierProvider<RealtimeEventsNotifier, int>(
  (ref) => RealtimeEventsNotifier(),
);
