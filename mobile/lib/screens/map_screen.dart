import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
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
  GoogleMapController? _mapController;
  bool _locationEnabled = false;

  @override
  void initState() {
    super.initState();
    _checkLocationPermission();
  }

  Future<void> _checkLocationPermission() async {
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
  }

  void _onCameraIdle() async {
    if (_mapController == null) return;
    
    // Haritanın merkezini ve yakınlaştırma seviyesini al
    final bounds = await _mapController!.getVisibleRegion();
    final centerLat = (bounds.northeast.latitude + bounds.southwest.latitude) / 2;
    final centerLon = (bounds.northeast.longitude + bounds.southwest.longitude) / 2;
    
    // Ekrana sığan genişliği hesapla (yaklaşık radiusKm)
    final radius = Geolocator.distanceBetween(
      centerLat, bounds.southwest.longitude,
      centerLat, bounds.northeast.longitude
    ) / 2000; // çap / 2 / 1000 -> km cinsinden yarıçap

    ref.read(mapViewStateProvider.notifier).state = MapViewState(
      center: LatLng(centerLat, centerLon),
      radiusKm: radius.clamp(1.0, 50.0), // Min 1km, Max 50km
    );
  }

  @override
  Widget build(BuildContext context) {
    // Verileri dinle
    final predictionsAsync = ref.watch(predictionsProvider);
    final eventsAsync = ref.watch(eventsProvider);

    // Heatmap dairelerini oluştur
    final Set<Circle> circles = predictionsAsync.when(
      data: (predictions) => CongestionOverlay.buildCircles(predictions),
      loading: () => {},
      error: (_, __) => {},
    );

    // Etkinlik marker'larını oluştur
    final Set<Marker> markers = eventsAsync.when(
      data: (events) {
        return events.map((event) => EventMarker.buildMarker(context, ref, event)).toSet();
      },
      loading: () => {},
      error: (_, __) => {},
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
              color: Theme.of(context).cardColor.withOpacity(0.9),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 4),
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
          GoogleMap(
            initialCameraPosition: const CameraPosition(
              target: LatLng(AppConstants.istanbulLat, AppConstants.istanbulLon),
              zoom: AppConstants.defaultZoom,
            ),
            myLocationEnabled: _locationEnabled,
            myLocationButtonEnabled: false, // Kendi butomumuzu kullanacağız
            mapToolbarEnabled: false,
            zoomControlsEnabled: false,
            circles: circles,
            markers: markers,
            onMapCreated: (controller) => _mapController = controller,
            onCameraIdle: _onCameraIdle,
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
                      BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 4),
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
          if (!_locationEnabled) {
            await _checkLocationPermission();
          }
          if (_locationEnabled && _mapController != null) {
            final pos = await Geolocator.getCurrentPosition();
            _mapController!.animateCamera(
              CameraUpdate.newLatLngZoom(
                LatLng(pos.latitude, pos.longitude),
                14,
              ),
            );
          }
        },
        child: const Icon(Icons.my_location),
      ),
    );
  }
}
