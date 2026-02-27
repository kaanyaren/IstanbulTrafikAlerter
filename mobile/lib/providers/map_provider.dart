import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../models/prediction.dart';
import '../models/event.dart';
import '../services/api_service.dart';
import '../core/constants.dart';

// State to hold map center and radius for data fetching
class MapViewState {
  final LatLng center;
  final double radiusKm;

  const MapViewState({
    required this.center,
    required this.radiusKm,
  });

  MapViewState copyWith({
    LatLng? center,
    double? radiusKm,
  }) {
    return MapViewState(
      center: center ?? this.center,
      radiusKm: radiusKm ?? this.radiusKm,
    );
  }
}

final mapViewStateProvider = StateProvider<MapViewState>((ref) {
  return MapViewState(
    center: LatLng(AppConstants.istanbulLat, AppConstants.istanbulLon),
    radiusKm: AppConstants.defaultRadiusKm,
  );
});

// Provider for fetching predictions based on current map view
final predictionsProvider = FutureProvider<List<Prediction>>((ref) async {
  final mapState = ref.watch(mapViewStateProvider);
  final api = ApiService.instance;
  
  return await api.getPredictions(
    mapState.center.latitude,
    mapState.center.longitude,
    mapState.radiusKm,
  );
});

// Provider for fetching events based on current map view
final eventsProvider = FutureProvider<List<TrafficEvent>>((ref) async {
  final mapState = ref.watch(mapViewStateProvider);
  final api = ApiService.instance;
  
  return await api.getEvents(
    lat: mapState.center.latitude,
    lon: mapState.center.longitude,
    radiusKm: mapState.radiusKm,
  );
});

// A provider for selected event details
final selectedEventProvider = StateProvider<TrafficEvent?>((ref) => null);
