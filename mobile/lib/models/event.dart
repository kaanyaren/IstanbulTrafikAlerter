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
  });

  factory TrafficEvent.fromJson(Map<String, dynamic> json) {
    return TrafficEvent(
      id: json['id'] as int,
      name: json['name'] as String,
      category: json['category'] as String,
      lat: (json['lat'] as num).toDouble(),
      lon: (json['lon'] as num).toDouble(),
      startTime: DateTime.parse(json['start_time'] as String),
      endTime: json['end_time'] != null ? DateTime.parse(json['end_time'] as String) : null,
      capacity: json['capacity'] as int?,
      trafficImpact: json['traffic_impact'] as int,
      venue: json['venue'] as String?,
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

  // Mock data for testing
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
        lat: 41.0750,
        lon: 29.0230,
        startTime: now.add(const Duration(hours: 5)),
        capacity: 15000,
        trafficImpact: 78,
        venue: 'Volkswagen Arena',
      ),
    ];
  }
}
