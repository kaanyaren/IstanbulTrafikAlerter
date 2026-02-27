import 'package:flutter/material.dart';

/// Open-Meteo API'den gelen hava durumu verilerini temsil eden modeller.

class CurrentWeather {
  final double temperature;
  final double apparentTemperature;
  final int relativeHumidity;
  final double precipitation;
  final double rain;
  final double showers;
  final double snowfall;
  final int weatherCode;
  final double windSpeed;
  final int windDirection;
  final int cloudCover;
  final bool isDay;
  final DateTime time;

  CurrentWeather({
    required this.temperature,
    required this.apparentTemperature,
    required this.relativeHumidity,
    required this.precipitation,
    required this.rain,
    required this.showers,
    required this.snowfall,
    required this.weatherCode,
    required this.windSpeed,
    required this.windDirection,
    required this.cloudCover,
    required this.isDay,
    required this.time,
  });

  factory CurrentWeather.fromJson(Map<String, dynamic> json) {
    return CurrentWeather(
      temperature: (json['temperature_2m'] as num).toDouble(),
      apparentTemperature: (json['apparent_temperature'] as num).toDouble(),
      relativeHumidity: (json['relative_humidity_2m'] as num).toInt(),
      precipitation: (json['precipitation'] as num).toDouble(),
      rain: (json['rain'] as num).toDouble(),
      showers: (json['showers'] as num).toDouble(),
      snowfall: (json['snowfall'] as num).toDouble(),
      weatherCode: (json['weather_code'] as num).toInt(),
      windSpeed: (json['wind_speed_10m'] as num).toDouble(),
      windDirection: (json['wind_direction_10m'] as num).toInt(),
      cloudCover: (json['cloud_cover'] as num).toInt(),
      isDay: (json['is_day'] as num).toInt() == 1,
      time: DateTime.parse(json['time'] as String),
    );
  }

  /// Yağış var mı? (yağmur, sağanak veya kar)
  bool get hasActivePrecipitation => precipitation > 0.0;

  /// Yağmur var mı?
  bool get isRaining => rain > 0.0 || showers > 0.0;

  /// Kar var mı?
  bool get isSnowing => snowfall > 0.0;
}

class DailyForecast {
  final DateTime date;
  final int weatherCode;
  final double tempMax;
  final double tempMin;
  final double precipitationSum;
  final double rainSum;
  final int precipitationProbabilityMax;
  final double windSpeedMax;
  final DateTime sunrise;
  final DateTime sunset;

  DailyForecast({
    required this.date,
    required this.weatherCode,
    required this.tempMax,
    required this.tempMin,
    required this.precipitationSum,
    required this.rainSum,
    required this.precipitationProbabilityMax,
    required this.windSpeedMax,
    required this.sunrise,
    required this.sunset,
  });
}

class HourlyForecast {
  final DateTime time;
  final double temperature;
  final int weatherCode;
  final double precipitation;
  final double rain;
  final int precipitationProbability;
  final double windSpeed;
  final int cloudCover;

  HourlyForecast({
    required this.time,
    required this.weatherCode,
    required this.temperature,
    required this.precipitation,
    required this.rain,
    required this.precipitationProbability,
    required this.windSpeed,
    required this.cloudCover,
  });
}

class WeatherData {
  final CurrentWeather current;
  final List<DailyForecast> dailyForecasts;
  final List<HourlyForecast> hourlyForecasts;
  final DateTime fetchedAt;

  WeatherData({
    required this.current,
    required this.dailyForecasts,
    required this.hourlyForecasts,
    DateTime? fetchedAt,
  }) : fetchedAt = fetchedAt ?? DateTime.now();
}

/// WMO Hava Durumu Kodları → Türkçe açıklama ve ikon
class WeatherCodeHelper {
  static String description(int code) {
    switch (code) {
      case 0:
        return 'Açık';
      case 1:
        return 'Çoğunlukla açık';
      case 2:
        return 'Parçalı bulutlu';
      case 3:
        return 'Kapalı';
      case 45:
        return 'Sisli';
      case 48:
        return 'Kırağılı sis';
      case 51:
        return 'Hafif çisenti';
      case 53:
        return 'Orta çisenti';
      case 55:
        return 'Yoğun çisenti';
      case 56:
        return 'Hafif donan çisenti';
      case 57:
        return 'Yoğun donan çisenti';
      case 61:
        return 'Hafif yağmur';
      case 63:
        return 'Orta yağmur';
      case 65:
        return 'Şiddetli yağmur';
      case 66:
        return 'Hafif donan yağmur';
      case 67:
        return 'Şiddetli donan yağmur';
      case 71:
        return 'Hafif kar';
      case 73:
        return 'Orta kar';
      case 75:
        return 'Yoğun kar';
      case 77:
        return 'Kar taneleri';
      case 80:
        return 'Hafif sağanak';
      case 81:
        return 'Orta sağanak';
      case 82:
        return 'Şiddetli sağanak';
      case 85:
        return 'Hafif kar sağanağı';
      case 86:
        return 'Şiddetli kar sağanağı';
      case 95:
        return 'Gök gürültülü fırtına';
      case 96:
        return 'Hafif dolu ile fırtına';
      case 99:
        return 'Şiddetli dolu ile fırtına';
      default:
        return 'Bilinmeyen ($code)';
    }
  }

  static IconData icon(int code, {bool isDay = true}) {
    // Returns Material Icons suitable for weather codes
    if (code == 0) return isDay ? Icons.wb_sunny : Icons.nightlight_round;
    if (code <= 3) return isDay ? Icons.wb_cloudy : Icons.nights_stay;
    if (code <= 48) return Icons.foggy;
    if (code <= 57) return Icons.grain;
    if (code <= 67) return Icons.water_drop;
    if (code <= 77) return Icons.ac_unit;
    if (code <= 82) return Icons.beach_access; // rain shower
    if (code <= 86) return Icons.ac_unit;
    if (code >= 95) return Icons.thunderstorm;
    return Icons.help_outline;
  }

  static Color color(int code) {
    if (code == 0) return const Color(0xFFFFA726); // sunny orange
    if (code <= 3) return const Color(0xFF78909C); // cloud grey
    if (code <= 48) return const Color(0xFF90A4AE); // fog
    if (code <= 57) return const Color(0xFF4FC3F7); // drizzle light blue
    if (code <= 67) return const Color(0xFF1976D2); // rain blue
    if (code <= 77) return const Color(0xFFB3E5FC); // snow light blue
    if (code <= 82) return const Color(0xFF0D47A1); // heavy rain
    if (code <= 86) return const Color(0xFF81D4FA); // snow shower
    if (code >= 95) return const Color(0xFFE65100); // thunderstorm
    return const Color(0xFF9E9E9E);
  }

  /// Yağış uyarısı seviyesi (trafik etkisi)
  static String precipitationTrafficImpact(int code) {
    if (code >= 95) return 'Fırtına nedeniyle trafik çok olumsuz etkilenebilir!';
    if (code >= 80) return 'Sağanak yağış trafiği olumsuz etkiliyor!';
    if (code >= 61) return 'Yağmur nedeniyle trafik yavaşlayabilir.';
    if (code >= 51) return 'Çisenti var, yollar kaygan olabilir.';
    if (code >= 71 && code <= 77) return 'Kar yağışı trafiği ciddi şekilde etkileyebilir!';
    if (code >= 85) return 'Kar sağanağı trafiği durma noktasına getirebilir!';
    return '';
  }

  /// Yağışlı bir hava kodu mu?
  static bool isPrecipitationCode(int code) {
    return code >= 51;
  }
}


