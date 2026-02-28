import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import '../models/prediction.dart';
import '../models/event.dart';

/// Supabase üzerinden veri okuma servisi.
/// PostgREST REST API ve RPC fonksiyonlarını kullanır.
class SupabaseService {
  static SupabaseService? _instance;
  late final SupabaseClient _client;

  SupabaseService._() {
    _client = Supabase.instance.client;
  }

  static SupabaseService get instance {
    _instance ??= SupabaseService._();
    return _instance!;
  }

  SupabaseClient get client => _client;

  // ── Predictions ───────────────────────────────────────────────────────────

  /// Belirtilen koordinata yakın tahminleri RPC ile getirir.
  Future<List<Prediction>> getPredictions(
    double lat,
    double lon,
    double radiusKm,
  ) async {
    try {
      final response = await _client.rpc('get_predictions_nearby', params: {
        'p_lat': lat,
        'p_lon': lon,
        'p_radius_km': radiusKm,
      });

      final list = response as List<dynamic>;
      final predictions = list.map((row) {
        final map = row as Map<String, dynamic>;
        return Prediction(
          zoneId: map['zone_id']?.hashCode ?? 0,
          lat: (map['zone_centroid_lat'] as num?)?.toDouble() ?? 0.0,
          lon: (map['zone_centroid_lon'] as num?)?.toDouble() ?? 0.0,
          score: (map['congestion_score'] as num?)?.toInt() ?? 0,
          timestamp:
              DateTime.tryParse(map['target_time'] ?? '') ?? DateTime.now(),
          label: scoreToLabel(map['congestion_score'] as int? ?? 0),
          zoneName: map['zone_name'] as String?,
        );
      }).toList();
      debugPrint('[SupabaseService] getPredictions ok: ${predictions.length}');
      return predictions;
    } catch (e) {
      debugPrint('[SupabaseService] getPredictions error: $e');
      // Supabase bağlantısı yoksa mock data döndür
      return Prediction.mockData();
    }
  }

  /// En güncel tahminleri getirir (tüm zone'lar için).
  Future<List<Prediction>> getLatestPredictions() async {
    try {
      final response = await _client.rpc('get_latest_predictions');

      final list = response as List<dynamic>;
      return list.map((row) {
        final map = row as Map<String, dynamic>;
        return Prediction(
          zoneId: map['zone_id']?.hashCode ?? 0,
          lat: (map['zone_centroid_lat'] as num?)?.toDouble() ?? 0.0,
          lon: (map['zone_centroid_lon'] as num?)?.toDouble() ?? 0.0,
          score: (map['congestion_score'] as num?)?.toInt() ?? 0,
          timestamp:
              DateTime.tryParse(map['target_time'] ?? '') ?? DateTime.now(),
          label: scoreToLabel(map['congestion_score'] as int? ?? 0),
          zoneName: map['zone_name'] as String?,
        );
      }).toList();
    } catch (e) {
      debugPrint('[SupabaseService] getLatestPredictions error: $e');
      return Prediction.mockData();
    }
  }

  // ── Events ────────────────────────────────────────────────────────────────

  /// Belirtilen koordinata yakın etkinlikleri RPC ile getirir.
  Future<List<TrafficEvent>> getEvents({
    double? lat,
    double? lon,
    double? radiusKm,
    String? category,
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final params = <String, dynamic>{
        'p_lat': lat ?? 41.0082,
        'p_lon': lon ?? 28.9784,
        'p_radius_km': radiusKm ?? 50.0,
      };
      if (category != null) params['p_category'] = category;
      if (startDate != null) {
        params['p_start_date'] = startDate.toIso8601String();
      }
      if (endDate != null) params['p_end_date'] = endDate.toIso8601String();

      final response = await _client.rpc('get_events_nearby', params: params);

      final list = response as List<dynamic>;
      final events = list
          .map((row) {
            final map = row as Map<String, dynamic>;
            final startTime = _parseEventDateTime(map['start_time']);
            if (startTime == null) {
              debugPrint(
                  '[SupabaseService] skipping event with invalid start_time: ${map['event_id']}');
              return null;
            }

            return TrafficEvent(
              id: map['event_id']?.hashCode ?? 0,
              name: map['name'] as String? ?? '',
              category: map['category'] as String? ?? 'other',
              lat: (map['lat'] as num?)?.toDouble() ?? 0.0,
              lon: (map['lon'] as num?)?.toDouble() ?? 0.0,
              startTime: startTime,
              endTime: _parseEventDateTime(map['end_time']),
              capacity: map['capacity'] as int?,
              trafficImpact: estimateTrafficImpact(map['capacity'] as int?),
              venue: map['venue_name'] as String?,
              source: map['source'] as String?,
            );
          })
          .whereType<TrafficEvent>()
          .toList();
      debugPrint('[SupabaseService] getEvents ok: ${events.length}');
      return events;
    } catch (e) {
      debugPrint('[SupabaseService] getEvents error: $e');
      return const [];
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  static String scoreToLabel(int score) {
    if (score <= 30) return 'Az';
    if (score <= 60) return 'Orta';
    if (score <= 80) return 'Yoğun';
    return 'Çok Yoğun';
  }

  static int estimateTrafficImpact(int? capacity) {
    if (capacity == null || capacity == 0) return 30;
    if (capacity > 50000) return 95;
    if (capacity > 20000) return 80;
    if (capacity > 5000) return 60;
    return 40;
  }

  static DateTime? _parseEventDateTime(dynamic value) {
    if (value == null) return null;
    final raw = value.toString().trim();
    if (raw.isEmpty) return null;

    final direct = DateTime.tryParse(raw);
    if (direct != null) return direct;

    final trDate = RegExp(
            r'^(\d{2})\.(\d{2})\.(\d{4})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?$')
        .firstMatch(raw);
    if (trDate != null) {
      final day = int.tryParse(trDate.group(1)!);
      final month = int.tryParse(trDate.group(2)!);
      final year = int.tryParse(trDate.group(3)!);
      final hour = int.tryParse(trDate.group(4) ?? '0');
      final minute = int.tryParse(trDate.group(5) ?? '0');
      final second = int.tryParse(trDate.group(6) ?? '0');

      if (day == null ||
          month == null ||
          year == null ||
          hour == null ||
          minute == null ||
          second == null) {
        return null;
      }
      try {
        return DateTime(year, month, day, hour, minute, second);
      } catch (_) {
        return null;
      }
    }

    return null;
  }
}
