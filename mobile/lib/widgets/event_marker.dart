import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/event.dart';
import '../providers/map_provider.dart';
import 'event_detail_sheet.dart';

class EventMarker {
  static Marker buildMarker(BuildContext context, WidgetRef ref, TrafficEvent event) {
    return Marker(
      markerId: MarkerId('event_${event.id}'),
      position: LatLng(event.lat, event.lon),
      infoWindow: InfoWindow(
        title: event.name,
        snippet: 'Trafik Etkisi: %${event.trafficImpact}',
      ),
      icon: BitmapDescriptor.defaultMarkerWithHue(
        event.trafficImpact > 70 
            ? BitmapDescriptor.hueRed 
            : (event.trafficImpact > 40 ? BitmapDescriptor.hueOrange : BitmapDescriptor.hueYellow),
      ),
      onTap: () {
        ref.read(selectedEventProvider.notifier).state = event;
        _showEventDetails(context, event);
      },
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
