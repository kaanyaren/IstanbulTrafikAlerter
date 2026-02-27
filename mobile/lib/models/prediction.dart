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

  // Mock data for testing — covers major Istanbul districts
  static List<Prediction> mockData() {
    final now = DateTime.now();
    return [
      // Anadolu yakası
      Prediction(zoneId: 1, lat: 40.9900, lon: 29.0300, score: 85, timestamp: now, label: 'Çok Yoğun', zoneName: 'Kadıköy'),
      Prediction(zoneId: 6, lat: 41.0230, lon: 29.0140, score: 55, timestamp: now, label: 'Orta', zoneName: 'Üsküdar'),
      Prediction(zoneId: 7, lat: 40.9370, lon: 29.1210, score: 30, timestamp: now, label: 'Az', zoneName: 'Maltepe'),
      Prediction(zoneId: 8, lat: 40.9830, lon: 29.0960, score: 90, timestamp: now, label: 'Çok Yoğun', zoneName: 'Ataşehir'),
      Prediction(zoneId: 9, lat: 40.9070, lon: 29.1900, score: 42, timestamp: now, label: 'Orta', zoneName: 'Pendik'),
      Prediction(zoneId: 10, lat: 40.9560, lon: 29.0620, score: 68, timestamp: now, label: 'Yoğun', zoneName: 'Kartal'),
      Prediction(zoneId: 11, lat: 41.0950, lon: 29.0700, score: 38, timestamp: now, label: 'Orta', zoneName: 'Beykoz'),
      // Avrupa yakası
      Prediction(zoneId: 2, lat: 41.0450, lon: 29.0100, score: 62, timestamp: now, label: 'Yoğun', zoneName: 'Beşiktaş'),
      Prediction(zoneId: 3, lat: 41.0600, lon: 28.9900, score: 45, timestamp: now, label: 'Orta', zoneName: 'Şişli'),
      Prediction(zoneId: 4, lat: 41.0160, lon: 28.9500, score: 20, timestamp: now, label: 'Az', zoneName: 'Fatih'),
      Prediction(zoneId: 5, lat: 41.0350, lon: 28.9770, score: 75, timestamp: now, label: 'Yoğun', zoneName: 'Beyoğlu'),
      Prediction(zoneId: 12, lat: 40.9800, lon: 28.8700, score: 78, timestamp: now, label: 'Yoğun', zoneName: 'Bakırköy'),
      Prediction(zoneId: 13, lat: 41.0850, lon: 28.8100, score: 52, timestamp: now, label: 'Orta', zoneName: 'Başakşehir'),
      Prediction(zoneId: 14, lat: 41.0400, lon: 28.8800, score: 88, timestamp: now, label: 'Çok Yoğun', zoneName: 'Bağcılar'),
      Prediction(zoneId: 15, lat: 40.9980, lon: 28.7900, score: 35, timestamp: now, label: 'Orta', zoneName: 'Avcılar'),
      Prediction(zoneId: 16, lat: 41.0700, lon: 28.9300, score: 60, timestamp: now, label: 'Orta', zoneName: 'Eyüpsultan'),
      // Köprü / Boğaz bölgesi
      Prediction(zoneId: 17, lat: 41.0452, lon: 29.0342, score: 95, timestamp: now, label: 'Çok Yoğun', zoneName: '15 Temmuz Köprüsü'),
      Prediction(zoneId: 18, lat: 41.0900, lon: 29.0600, score: 82, timestamp: now, label: 'Çok Yoğun', zoneName: 'FSM Köprüsü'),
    ];
  }
}
