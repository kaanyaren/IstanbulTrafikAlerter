import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';

import '../core/constants.dart';
import '../providers/map_provider.dart';
import '../widgets/congestion_overlay.dart';
import '../widgets/event_marker.dart';

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  final MapController _mapController = MapController();
  bool _locationEnabled = false;

  @override
  void initState() {
    super.initState();
    _checkLocationPermission();
  }

  Future<void> _checkLocationPermission() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) return;

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) return;
      }

      if (permission == LocationPermission.deniedForever) return;

      setState(() {
        _locationEnabled = true;
      });
    } catch (e) {
      debugPrint('Location permission check failed: $e');
    }
  }

  void _onPositionChanged(MapCamera camera, bool hasGesture) {
    if (!hasGesture) return;

    final center = camera.center;
    final bounds = camera.visibleBounds;

    // Approximate radius in km from visible bounds
    final radius = const Distance().as(
      LengthUnit.Kilometer,
      LatLng(center.latitude, bounds.west),
      LatLng(center.latitude, bounds.east),
    ) / 2;

    ref.read(mapViewStateProvider.notifier).state = MapViewState(
      center: center,
      radiusKm: radius.clamp(1.0, 50.0),
    );
  }

  @override
  Widget build(BuildContext context) {
    // Verileri dinle
    final predictionsAsync = ref.watch(predictionsProvider);
    final eventsAsync = ref.watch(eventsProvider);

    // Heatmap dairelerini oluştur
    final circleMarkers = predictionsAsync.when(
      data: (predictions) => CongestionOverlay.buildCircles(predictions),
      loading: () => <CircleMarker>[],
      error: (_, __) => <CircleMarker>[],
    );

    // Etkinlik marker'larını oluştur
    final markers = eventsAsync.when(
      data: (events) {
        return events.map((event) => EventMarker.buildMarker(context, ref, event)).toList();
      },
      loading: () => <Marker>[],
      error: (_, __) => <Marker>[],
    );

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16, top: 8, bottom: 8),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor.withAlpha(230),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(color: Colors.black.withAlpha(25), blurRadius: 4),
              ],
            ),
            child: IconButton(
              icon: const Icon(Icons.settings),
              onPressed: () => context.push('/settings'),
            ),
          ),
        ],
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: LatLng(AppConstants.istanbulLat, AppConstants.istanbulLon),
              initialZoom: AppConstants.defaultZoom,
              onPositionChanged: _onPositionChanged,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.istanbultrafficalerter.app',
              ),
              CircleLayer(circles: circleMarkers),
              MarkerLayer(markers: markers),
            ],
          ),

          // Legend overlay
          Positioned(
            bottom: 100,
            left: 16,
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Theme.of(context).cardColor.withAlpha(230),
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(color: Colors.black.withAlpha(25), blurRadius: 4),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('Trafik Yoğunluğu', style: Theme.of(context).textTheme.labelSmall?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  _legendItem(const Color(0xFF34A853), 'Az (0-30)'),
                  _legendItem(const Color(0xFFFBBC05), 'Orta (31-60)'),
                  _legendItem(const Color(0xFFFF6D00), 'Yoğun (61-80)'),
                  _legendItem(const Color(0xFFEA4335), 'Çok Yoğun (81-100)'),
                ],
              ),
            ),
          ),

          // Yükleniyor göstergesi
          if (predictionsAsync.isLoading || eventsAsync.isLoading)
            Positioned(
              top: MediaQuery.of(context).padding.top + 60,
              left: 0,
              right: 0,
              child: Center(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Theme.of(context).cardColor,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(color: Colors.black.withAlpha(25), blurRadius: 4),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const SizedBox(
                        width: 16, height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Veriler güncelleniyor...',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          try {
            if (!_locationEnabled) {
              await _checkLocationPermission();
            }
            if (_locationEnabled) {
              final pos = await Geolocator.getCurrentPosition();
              _mapController.move(
                LatLng(pos.latitude, pos.longitude),
                14,
              );
            }
          } catch (e) {
            debugPrint('Location error: $e');
          }
        },
        child: const Icon(Icons.my_location),
      ),
    );
  }

  Widget _legendItem(Color color, String label) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 14,
            height: 14,
            decoration: BoxDecoration(
              color: color.withAlpha(90),
              border: Border.all(color: color, width: 1.5),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(fontSize: 11)),
        ],
      ),
    );
  }
}
