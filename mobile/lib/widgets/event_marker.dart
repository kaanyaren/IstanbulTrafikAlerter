import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../models/event.dart';
import '../core/theme.dart';
import '../providers/map_provider.dart';
import 'event_detail_sheet.dart';

class EventMarker {
  static Color categoryColor(String category) {
    final normalized = category.toLowerCase();

    if (_matchesAny(normalized,
        ['spor', 'müsabaka', 'match', 'sport', 'futbol', 'basketbol'])) {
      return AppTheme.secondaryColor;
    }

    if (_matchesAny(
        normalized, ['konser', 'müzik', 'music', 'festival', 'show'])) {
      return AppTheme.warningColor;
    }

    if (_matchesAny(
        normalized, ['siyasi', 'politic', 'miting', 'protesto', 'rally'])) {
      return AppTheme.errorColor;
    }

    return AppTheme.primaryColor;
  }

  static bool _matchesAny(String text, List<String> keywords) {
    for (final keyword in keywords) {
      if (text.contains(keyword)) {
        return true;
      }
    }
    return false;
  }

  static Marker buildMarker(
      BuildContext context, WidgetRef ref, TrafficEvent event) {
    final markerColor = categoryColor(event.category);

    return Marker(
      point: LatLng(event.lat, event.lon),
      width: 52,
      height: 52,
      child: GestureDetector(
        onTap: () {
          ref.read(selectedEventProvider.notifier).state = event;
          _showEventDetails(context, event);
        },
        child: Tooltip(
          message:
              '${event.name}\nKategori: ${event.category}\nTrafik Etkisi: %${event.trafficImpact}',
          child: Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: markerColor.withAlpha(55),
              border:
                  Border.all(color: Colors.white.withAlpha(230), width: 1.8),
              boxShadow: [
                BoxShadow(
                  color: markerColor.withAlpha(130),
                  blurRadius: 12,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: Center(
              child: Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: markerColor,
                ),
                child: Center(
                  child: Text(
                    event.categoryEmoji,
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  static void _showEventDetails(BuildContext context, TrafficEvent event) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => EventDetailSheet(event: event),
    );
  }
}
