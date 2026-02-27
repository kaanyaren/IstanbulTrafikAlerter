import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/weather.dart';
import '../services/weather_service.dart';

/// İstanbul hava durumu verisini sağlayan provider.
/// Her 15 dakikada bir otomatik yenilenir.
final weatherProvider = FutureProvider.autoDispose<WeatherData>((ref) async {
  final weather = await WeatherService.instance.getIstanbulWeather();
  return weather;
});

/// Anlık yağış durumunu izleyen provider (trafik uyarısı için).
final isRainingProvider = Provider.autoDispose<bool>((ref) {
  final weatherAsync = ref.watch(weatherProvider);
  return weatherAsync.whenOrNull(
        data: (data) => data.current.hasActivePrecipitation,
      ) ??
      false;
});

/// Anlık hava kodu provider (uyarı mesajı için).
final currentWeatherCodeProvider = Provider.autoDispose<int?>((ref) {
  final weatherAsync = ref.watch(weatherProvider);
  return weatherAsync.whenOrNull(
    data: (data) => data.current.weatherCode,
  );
});
