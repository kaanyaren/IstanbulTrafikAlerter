import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../models/weather.dart';

/// Open-Meteo API üzerinden İstanbul hava durumu verilerini çeken servis.
/// Ücretsiz, API key gerektirmez.
class WeatherService {
  static WeatherService? _instance;
  late final Dio _dio;

  // İstanbul koordinatları
  static const double _istanbulLat = 41.0082;
  static const double _istanbulLon = 28.9784;
  static const String _baseUrl = 'https://api.open-meteo.com/v1';

  WeatherService._() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    ));
  }

  static WeatherService get instance {
    _instance ??= WeatherService._();
    return _instance!;
  }

  /// İstanbul için anlık + 3 günlük (bugün + 2 gün) hava durumu verisi çeker.
  Future<WeatherData> getIstanbulWeather() async {
    try {
      final response = await _dio.get('/forecast', queryParameters: {
        'latitude': _istanbulLat,
        'longitude': _istanbulLon,
        'current': [
          'temperature_2m',
          'relative_humidity_2m',
          'apparent_temperature',
          'precipitation',
          'rain',
          'showers',
          'snowfall',
          'weather_code',
          'wind_speed_10m',
          'wind_direction_10m',
          'cloud_cover',
          'is_day',
        ].join(','),
        'hourly': [
          'temperature_2m',
          'weather_code',
          'precipitation',
          'rain',
          'precipitation_probability',
          'wind_speed_10m',
          'cloud_cover',
        ].join(','),
        'daily': [
          'weather_code',
          'temperature_2m_max',
          'temperature_2m_min',
          'precipitation_sum',
          'rain_sum',
          'precipitation_probability_max',
          'wind_speed_10m_max',
          'sunrise',
          'sunset',
        ].join(','),
        'timezone': 'Europe/Istanbul',
        'forecast_days': 3,
      });

      final data = response.data as Map<String, dynamic>;
      return _parseWeatherData(data);
    } on DioException catch (e) {
      debugPrint('[WeatherService] API error: ${e.message}');
      rethrow;
    } catch (e) {
      debugPrint('[WeatherService] Parse error: $e');
      rethrow;
    }
  }

  WeatherData _parseWeatherData(Map<String, dynamic> data) {
    // --- Current ---
    final currentJson = data['current'] as Map<String, dynamic>;
    final current = CurrentWeather.fromJson(currentJson);

    // --- Daily ---
    final dailyJson = data['daily'] as Map<String, dynamic>;
    final dailyTimes = (dailyJson['time'] as List).cast<String>();
    final dailyForecasts = <DailyForecast>[];

    for (int i = 0; i < dailyTimes.length; i++) {
      dailyForecasts.add(DailyForecast(
        date: DateTime.parse(dailyTimes[i]),
        weatherCode: (dailyJson['weather_code'] as List)[i] as int,
        tempMax: ((dailyJson['temperature_2m_max'] as List)[i] as num).toDouble(),
        tempMin: ((dailyJson['temperature_2m_min'] as List)[i] as num).toDouble(),
        precipitationSum: ((dailyJson['precipitation_sum'] as List)[i] as num).toDouble(),
        rainSum: ((dailyJson['rain_sum'] as List)[i] as num).toDouble(),
        precipitationProbabilityMax:
            ((dailyJson['precipitation_probability_max'] as List)[i] as num).toInt(),
        windSpeedMax: ((dailyJson['wind_speed_10m_max'] as List)[i] as num).toDouble(),
        sunrise: DateTime.parse((dailyJson['sunrise'] as List)[i] as String),
        sunset: DateTime.parse((dailyJson['sunset'] as List)[i] as String),
      ));
    }

    // --- Hourly ---
    final hourlyJson = data['hourly'] as Map<String, dynamic>;
    final hourlyTimes = (hourlyJson['time'] as List).cast<String>();
    final hourlyForecasts = <HourlyForecast>[];

    for (int i = 0; i < hourlyTimes.length; i++) {
      hourlyForecasts.add(HourlyForecast(
        time: DateTime.parse(hourlyTimes[i]),
        temperature: ((hourlyJson['temperature_2m'] as List)[i] as num).toDouble(),
        weatherCode: (hourlyJson['weather_code'] as List)[i] as int,
        precipitation: ((hourlyJson['precipitation'] as List)[i] as num).toDouble(),
        rain: ((hourlyJson['rain'] as List)[i] as num).toDouble(),
        precipitationProbability:
            ((hourlyJson['precipitation_probability'] as List)[i] as num).toInt(),
        windSpeed: ((hourlyJson['wind_speed_10m'] as List)[i] as num).toDouble(),
        cloudCover: ((hourlyJson['cloud_cover'] as List)[i] as num).toInt(),
      ));
    }

    return WeatherData(
      current: current,
      dailyForecasts: dailyForecasts,
      hourlyForecasts: hourlyForecasts,
    );
  }
}
