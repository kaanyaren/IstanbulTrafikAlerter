import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../models/prediction.dart';
import '../core/theme.dart';

class CongestionOverlay {
  static Set<Circle> buildCircles(List<Prediction> predictions) {
    return predictions.map((p) {
      Color color = AppTheme.congestionColor(p.score);
      
      return Circle(
        circleId: CircleId('zone_${p.zoneId}'),
        center: LatLng(p.lat, p.lon),
        radius: 800, // 800m
        fillColor: color.withOpacity(0.35),
        strokeColor: color.withOpacity(0.8),
        strokeWidth: 2,
        zIndex: 1, // overlay
      );
    }).toSet();
  }
}
