class Prediction {
  final int zoneId;
  final double lat;
  final double lon;
  final int score;
  final DateTime timestamp;
  final String label;
  final String? zoneName;

  const Prediction({
    required this.zoneId,
    required this.lat,
    required this.lon,
    required this.score,
    required this.timestamp,
    required this.label,
    this.zoneName,
  });

  factory Prediction.fromJson(Map<String, dynamic> json) {
    return Prediction(
      zoneId: json['zone_id'] as int,
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      score: json['score'] as int,
      timestamp: DateTime.parse(json['timestamp'] as String),
      label: json['label'] as String,
      zoneName: json['zone_name'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'zone_id': zoneId,
        'lat': lat,
        'lon': lon,
        'score': score,
        'timestamp': timestamp.toIso8601String(),
        'label': label,
        'zone_name': zoneName,
      };

  // Mock data for testing
  static List<Prediction> mockData() {
    final now = DateTime.now();
    return [
      Prediction(zoneId: 1, lat: 40.9900, lon: 29.0300, score: 85, timestamp: now, label: 'Çok Yoğun', zoneName: 'Kadıköy'),
      Prediction(zoneId: 2, lat: 41.0450, lon: 29.0100, score: 62, timestamp: now, label: 'Yoğun', zoneName: 'Beşiktaş'),
      Prediction(zoneId: 3, lat: 41.0600, lon: 28.9900, score: 45, timestamp: now, label: 'Orta', zoneName: 'Şişli'),
      Prediction(zoneId: 4, lat: 41.0160, lon: 28.9500, score: 20, timestamp: now, label: 'Az', zoneName: 'Fatih'),
      Prediction(zoneId: 5, lat: 41.0350, lon: 28.9770, score: 75, timestamp: now, label: 'Yoğun', zoneName: 'Beyoğlu'),
      Prediction(zoneId: 6, lat: 41.0230, lon: 29.0140, score: 55, timestamp: now, label: 'Orta', zoneName: 'Üsküdar'),
      Prediction(zoneId: 7, lat: 40.9370, lon: 29.1210, score: 30, timestamp: now, label: 'Az', zoneName: 'Maltepe'),
      Prediction(zoneId: 8, lat: 40.9830, lon: 29.0960, score: 90, timestamp: now, label: 'Çok Yoğun', zoneName: 'Ataşehir'),
    ];
  }
}
