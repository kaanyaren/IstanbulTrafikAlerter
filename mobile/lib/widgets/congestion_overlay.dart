import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/prediction.dart';
import '../core/theme.dart';

class CongestionOverlay {
  static List<CircleMarker> buildCircles(List<Prediction> predictions, {bool isDark = true}) {
    final List<CircleMarker> circles = [];

    for (final p in predictions) {
      final Color color = AppTheme.congestionColor(p.score);
      // Outer glow — larger, more transparent
      circles.add(CircleMarker(
        point: LatLng(p.lat, p.lon),
        radius: 60,
        color: color.withAlpha(isDark ? 40 : 30),
        borderColor: Colors.transparent,
        borderStrokeWidth: 0,
        useRadiusInMeter: false,
      ));
      // Inner core — smaller, more opaque
      circles.add(CircleMarker(
        point: LatLng(p.lat, p.lon),
        radius: 35,
        color: color.withAlpha(isDark ? 120 : 80),
        borderColor: color.withAlpha(isDark ? 220 : 180),
        borderStrokeWidth: 2,
        useRadiusInMeter: false,
      ));
    }

    return circles;
  }
}
