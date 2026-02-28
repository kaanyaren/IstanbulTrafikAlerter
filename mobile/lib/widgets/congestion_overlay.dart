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
      // Outer glow — larger, more transparent
      circles.add(CircleMarker(
        point: LatLng(p.lat, p.lon),
        radius: 46,
        color: color.withAlpha(isDark ? 26 : 20),
        borderColor: Colors.transparent,
        borderStrokeWidth: 0,
        useRadiusInMeter: false,
      ));
      // Inner core — smaller, more opaque
      circles.add(CircleMarker(
        point: LatLng(p.lat, p.lon),
        radius: 24,
        color: color.withAlpha(isDark ? 92 : 70),
        borderColor: color.withAlpha(isDark ? 130 : 110),
        borderStrokeWidth: 1.5,
        useRadiusInMeter: false,
      ));
    }

    return circles;
  }
}
