import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../models/event.dart';
import '../core/theme.dart';
import '../providers/map_provider.dart';
import 'event_detail_sheet.dart';

class EventMarker {
  static Marker buildMarker(BuildContext context, WidgetRef ref, TrafficEvent event) {
    Color markerColor = event.trafficImpact > 70
        ? AppTheme.errorColor
        : (event.trafficImpact > 40 ? AppTheme.warningColor : AppTheme.secondaryColor);

    return Marker(
      point: LatLng(event.lat, event.lon),
      width: 44,
      height: 44,
      child: GestureDetector(
        onTap: () {
          ref.read(selectedEventProvider.notifier).state = event;
          _showEventDetails(context, event);
        },
        child: Tooltip(
          message: '${event.name}\nTrafik Etkisi: %${event.trafficImpact}',
          child: Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: markerColor.withAlpha(40),
              border: Border.all(color: markerColor, width: 2),
              boxShadow: [
                BoxShadow(color: markerColor.withAlpha(80), blurRadius: 8, spreadRadius: 1),
              ],
            ),
            child: Center(
              child: Text(
                event.categoryEmoji,
                style: const TextStyle(fontSize: 20),
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
