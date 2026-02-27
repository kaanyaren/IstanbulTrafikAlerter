import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../models/prediction.dart';
import '../core/theme.dart';

class CongestionOverlay {
  static List<CircleMarker> buildCircles(List<Prediction> predictions) {
    return predictions.map((p) {
      Color color = AppTheme.congestionColor(p.score);

      return CircleMarker(
        point: LatLng(p.lat, p.lon),
        radius: 45,
        color: color.withAlpha(90),
        borderColor: color.withAlpha(200),
        borderStrokeWidth: 2,
        useRadiusInMeter: false,
      );
    }).toList();
  }
}
