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
      final double coreRadius = _radiusByScore(p.score);
      final LatLng point = LatLng(p.lat, p.lon);

      // Outer halo
      circles.add(CircleMarker(
        point: point,
        radius: coreRadius * 3.0,
        color: color.withAlpha(isDark ? 34 : 24),
        borderColor: color.withAlpha(isDark ? 45 : 30),
        borderStrokeWidth: 0.8,
        useRadiusInMeter: true,
      ));

      // Mid halo
      circles.add(CircleMarker(
        point: point,
        radius: coreRadius * 1.9,
        color: color.withAlpha(isDark ? 66 : 48),
        borderColor: color.withAlpha(isDark ? 80 : 56),
        borderStrokeWidth: 1.2,
        useRadiusInMeter: true,
      ));

      // Core
      circles.add(CircleMarker(
        point: point,
        radius: coreRadius,
        color: color.withAlpha(isDark ? 132 : 110),
        borderColor: Colors.white.withAlpha(isDark ? 185 : 200),
        borderStrokeWidth: 1.6,
        useRadiusInMeter: true,
      ));
    }

    return circles;
  }

  static double _radiusByScore(int score) {
    if (score >= 90) return 260;
    if (score >= 75) return 210;
    if (score >= 60) return 170;
    if (score >= 40) return 130;
    return 95;
  }
}
