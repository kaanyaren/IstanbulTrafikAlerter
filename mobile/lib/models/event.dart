class TrafficEvent {
  final int id;
  final String name;
  final String category;
  final double lat;
  final double lon;
  final DateTime startTime;
  final DateTime? endTime;
  final int? capacity;
  final int trafficImpact; // 0-100
  final String? venue;
  final String? source;

  const TrafficEvent({
    required this.id,
    required this.name,
    required this.category,
    required this.lat,
    required this.lon,
    required this.startTime,
    this.endTime,
    this.capacity,
    required this.trafficImpact,
    this.venue,
    this.source,
  });

  factory TrafficEvent.fromJson(Map<String, dynamic> json) {
    return TrafficEvent(
      id: json['id'] as int,
      name: json['name'] as String,
      category: json['category'] as String,
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      startTime: DateTime.parse(json['start_time'] as String),
      endTime: json['end_time'] != null
          ? DateTime.parse(json['end_time'] as String)
          : null,
      capacity: json['capacity'] as int?,
      trafficImpact: json['traffic_impact'] as int,
      venue: json['venue'] as String?,
      source: json['source'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'category': category,
        'lat': lat,
        'lon': lon,
        'start_time': startTime.toIso8601String(),
        'end_time': endTime?.toIso8601String(),
        'capacity': capacity,
        'traffic_impact': trafficImpact,
        'venue': venue,
        'source': source,
      };

  String get categoryEmoji {
    switch (category.toLowerCase()) {
      case 'spor':
        return '⚽';
      case 'müzik':
      case 'konser':
        return '🎵';
      case 'kültür':
      case 'sergi':
        return '🎨';
      case 'festival':
        return '🎉';
      case 'iş':
      case 'kongre':
        return '💼';
      default:
        return '📍';
    }
  }

  // Mock data for testing — diverse events across Istanbul
  static List<TrafficEvent> mockData() {
    final now = DateTime.now();
    return [
      TrafficEvent(
        id: 1,
        name: 'Galatasaray - Fenerbahçe Derbisi',
        category: 'Spor',
        lat: 40.9890,
        lon: 28.9360,
        startTime: now.add(const Duration(hours: 3)),
        capacity: 52000,
        trafficImpact: 92,
        venue: 'Rams Park',
      ),
      TrafficEvent(
        id: 2,
        name: 'İstanbul Film Festivali',
        category: 'Kültür',
        lat: 41.0330,
        lon: 28.9850,
        startTime: now.add(const Duration(hours: 1)),
        capacity: 800,
        trafficImpact: 45,
        venue: 'Atlas Sineması',
      ),
      TrafficEvent(
        id: 3,
        name: 'Tarkan Konseri',
        category: 'Müzik',
        lat: 41.1060,
        lon: 29.0520,
        startTime: now.add(const Duration(hours: 5)),
        capacity: 15000,
        trafficImpact: 78,
        venue: 'Türk Telekom Stadyumu',
      ),
      TrafficEvent(
        id: 4,
        name: 'Web Summit İstanbul',
        category: 'Kongre',
        lat: 40.9830,
        lon: 29.1240,
        startTime: now.add(const Duration(hours: 2)),
        capacity: 5000,
        trafficImpact: 60,
        venue: 'İstanbul Fuar Merkezi',
      ),
      TrafficEvent(
        id: 5,
        name: 'Kadıköy Sokak Festivali',
        category: 'Festival',
        lat: 40.9910,
        lon: 29.0260,
        startTime: now.add(const Duration(hours: 4)),
        capacity: 10000,
        trafficImpact: 70,
        venue: 'Bahariye Caddesi',
      ),
      TrafficEvent(
        id: 6,
        name: 'İstanbul Maratonu',
        category: 'Spor',
        lat: 41.0450,
        lon: 29.0340,
        startTime: now.add(const Duration(hours: 6)),
        endTime: now.add(const Duration(hours: 12)),
        capacity: 40000,
        trafficImpact: 95,
        venue: '15 Temmuz Köprüsü',
      ),
    ];
  }
}
