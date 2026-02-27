import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/weather.dart';
import '../providers/weather_provider.dart';

class WeatherScreen extends ConsumerWidget {
  const WeatherScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final weatherAsync = ref.watch(weatherProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('İstanbul Hava Durumu'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Yenile',
            onPressed: () => ref.invalidate(weatherProvider),
          ),
        ],
      ),
      body: weatherAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => _buildErrorView(context, ref, error),
        data: (weather) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(weatherProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // ── Anlık Hava Durumu Kartı ──
              _buildCurrentWeatherCard(context, weather.current, isDark),
              const SizedBox(height: 16),

              // ── Yağış Trafik Uyarısı ──
              if (WeatherCodeHelper.isPrecipitationCode(
                  weather.current.weatherCode))
                _buildTrafficAlertCard(context, weather.current),
              if (WeatherCodeHelper.isPrecipitationCode(
                  weather.current.weatherCode))
                const SizedBox(height: 16),

              // ── Saatlik Tahmin ──
              _buildSectionTitle(context, 'Saatlik Tahmin'),
              const SizedBox(height: 8),
              _buildHourlyForecast(context, weather.hourlyForecasts, isDark),
              const SizedBox(height: 20),

              // ── Günlük Tahmin ──
              _buildSectionTitle(context, 'Günlük Tahmin'),
              const SizedBox(height: 8),
              ...weather.dailyForecasts
                  .map((day) => _buildDailyCard(context, day, isDark)),
              const SizedBox(height: 16),

              // ── Veri Kaynağı ──
              Center(
                child: Text(
                  'Veri: Open-Meteo.com • Güncelleme: ${_formatTime(weather.fetchedAt)}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: Colors.grey,
                  ),
                ),
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildErrorView(BuildContext context, WidgetRef ref, Object error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.cloud_off, size: 64, color: Colors.grey),
            const SizedBox(height: 16),
            Text(
              'Hava durumu verileri yüklenemedi',
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              error.toString(),
              style: const TextStyle(color: Colors.grey, fontSize: 12),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => ref.invalidate(weatherProvider),
              icon: const Icon(Icons.refresh),
              label: const Text('Tekrar Dene'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCurrentWeatherCard(
      BuildContext context, CurrentWeather current, bool isDark) {
    final theme = Theme.of(context);
    final weatherColor = WeatherCodeHelper.color(current.weatherCode);

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              weatherColor.withAlpha(isDark ? 80 : 40),
              isDark ? theme.cardColor : Colors.white,
            ],
          ),
        ),
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Üst: ikon + sıcaklık
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  WeatherCodeHelper.icon(current.weatherCode,
                      isDay: current.isDay),
                  size: 56,
                  color: weatherColor,
                ),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${current.temperature.round()}°C',
                      style: theme.textTheme.displaySmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      WeatherCodeHelper.description(current.weatherCode),
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: weatherColor,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Hissedilen: ${current.apparentTemperature.round()}°C',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 20),
            // Alt: detay grid
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildDetailItem(
                    Icons.water_drop, '${current.relativeHumidity}%', 'Nem'),
                _buildDetailItem(
                    Icons.air, '${current.windSpeed.round()} km/s', 'Rüzgar'),
                _buildDetailItem(
                    Icons.cloud, '${current.cloudCover}%', 'Bulut'),
                _buildDetailItem(
                    Icons.umbrella, '${current.precipitation} mm', 'Yağış'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailItem(IconData icon, String value, String label) {
    return Column(
      children: [
        Icon(icon, size: 22, color: Colors.grey[500]),
        const SizedBox(height: 4),
        Text(value,
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        Text(label, style: TextStyle(color: Colors.grey[500], fontSize: 11)),
      ],
    );
  }

  Widget _buildTrafficAlertCard(BuildContext context, CurrentWeather current) {
    final impact =
        WeatherCodeHelper.precipitationTrafficImpact(current.weatherCode);
    if (impact.isEmpty) return const SizedBox.shrink();

    final isHeavy = current.weatherCode >= 63 ||
        (current.weatherCode >= 73 && current.weatherCode <= 77) ||
        current.weatherCode >= 80;

    return Card(
      elevation: 3,
      color: isHeavy ? const Color(0xFFFFF3E0) : const Color(0xFFE3F2FD),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              isHeavy ? Icons.warning_amber_rounded : Icons.info_outline,
              color: isHeavy ? Colors.orange[800] : Colors.blue[700],
              size: 32,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Yağışlı Hava Trafik Uyarısı',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: isHeavy ? Colors.orange[900] : Colors.blue[900],
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    impact,
                    style: TextStyle(
                      fontSize: 13,
                      color: isHeavy ? Colors.orange[800] : Colors.blue[800],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
    );
  }

  Widget _buildHourlyForecast(
      BuildContext context, List<HourlyForecast> forecasts, bool isDark) {
    // Sadece şimdiden itibaren 24 saat göster
    final now = DateTime.now();
    final upcoming = forecasts
        .where((h) => h.time.isAfter(now.subtract(const Duration(hours: 1))))
        .take(24)
        .toList();

    return SizedBox(
      height: 130,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: upcoming.length,
        separatorBuilder: (_, __) => const SizedBox(width: 4),
        itemBuilder: (context, index) {
          final hour = upcoming[index];
          final isNow = index == 0;
          return Container(
            width: 68,
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 6),
            decoration: BoxDecoration(
              color: isNow
                  ? Theme.of(context).colorScheme.primary.withAlpha(30)
                  : (isDark ? Colors.grey[850] : Colors.grey[100]),
              borderRadius: BorderRadius.circular(14),
              border: isNow
                  ? Border.all(
                      color: Theme.of(context).colorScheme.primary, width: 1.5)
                  : null,
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                Text(
                  isNow
                      ? 'Şimdi'
                      : '${hour.time.hour.toString().padLeft(2, '0')}:00',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: isNow ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
                Icon(
                  WeatherCodeHelper.icon(hour.weatherCode),
                  size: 24,
                  color: WeatherCodeHelper.color(hour.weatherCode),
                ),
                Text(
                  '${hour.temperature.round()}°',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
                if (hour.precipitationProbability > 0)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.water_drop, size: 10, color: Colors.blue[400]),
                      Text(
                        '${hour.precipitationProbability}%',
                        style: TextStyle(fontSize: 10, color: Colors.blue[400]),
                      ),
                    ],
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDailyCard(BuildContext context, DailyForecast day, bool isDark) {
    final theme = Theme.of(context);
    final dayName = _dayName(day.date);
    final weatherColor = WeatherCodeHelper.color(day.weatherCode);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            // Gün
            SizedBox(
              width: 70,
              child: Text(
                dayName,
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            // İkon
            Icon(
              WeatherCodeHelper.icon(day.weatherCode),
              color: weatherColor,
              size: 28,
            ),
            const SizedBox(width: 8),
            // Yağış olasılığı
            SizedBox(
              width: 48,
              child: day.precipitationProbabilityMax > 0
                  ? Row(
                      children: [
                        Icon(Icons.water_drop,
                            size: 14, color: Colors.blue[400]),
                        Text(
                          '${day.precipitationProbabilityMax}%',
                          style:
                              TextStyle(fontSize: 12, color: Colors.blue[400]),
                        ),
                      ],
                    )
                  : const SizedBox.shrink(),
            ),
            const Spacer(),
            // Sıcaklık aralığı
            Text(
              '${day.tempMin.round()}°',
              style: TextStyle(
                color: Colors.blue[300],
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(width: 4),
            // Sıcaklık barı
            SizedBox(
              width: 60,
              child: _buildTempBar(day.tempMin, day.tempMax),
            ),
            const SizedBox(width: 4),
            Text(
              '${day.tempMax.round()}°',
              style: TextStyle(
                color: Colors.orange[400],
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTempBar(double min, double max) {
    return Container(
      height: 6,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(3),
        gradient: LinearGradient(
          colors: [
            Colors.blue[300]!,
            Colors.orange[300]!,
          ],
        ),
      ),
    );
  }

  String _dayName(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final target = DateTime(date.year, date.month, date.day);
    final diff = target.difference(today).inDays;

    if (diff == 0) return 'Bugün';
    if (diff == 1) return 'Yarın';

    const days = [
      'Pazartesi',
      'Salı',
      'Çarşamba',
      'Perşembe',
      'Cuma',
      'Cumartesi',
      'Pazar'
    ];
    return days[date.weekday - 1];
  }

  String _formatTime(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }
}
