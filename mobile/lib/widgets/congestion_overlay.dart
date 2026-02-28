import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/prediction.dart';
import '../core/theme.dart';

class CongestionOverlay {
  static List<CircleMarker> buildCircles(List<Prediction> predictions,
      {bool isDark = true}) {
    final List<CircleMarker> circles = [];

    for (final p in predictions) {
      final Color color = AppTheme.congestionColor(p.score);

      // Single soft halo — small, very transparent, glassy
      circles.add(CircleMarker(
        point: LatLng(p.lat, p.lon),
        radius: 20,
        color: color.withAlpha(isDark ? 16 : 10),
        borderColor: color.withAlpha(isDark ? 20 : 14),
        borderStrokeWidth: 0.5,
        useRadiusInMeter: false,
      ));
    }

    return circles;
  }
}
