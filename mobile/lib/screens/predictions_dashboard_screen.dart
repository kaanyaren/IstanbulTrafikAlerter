import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/theme.dart';
import '../models/event.dart';
import '../providers/map_provider.dart';

class PredictionsDashboardScreen extends ConsumerWidget {
  const PredictionsDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final eventsAsync = ref.watch(eventsProvider);
    final cachedEvents = ref.watch(eventsCacheProvider);
    final events = eventsAsync.valueOrNull ?? cachedEvents;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Etkinlik Paneli'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(eventsProvider),
          ),
        ],
      ),
      body: events.isEmpty && eventsAsync.isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: () async => ref.invalidate(eventsProvider),
              child: ListView(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                children: [
                  _SummaryCard(events: events),
                  const SizedBox(height: 16),
                  Text(
                    'Çekilen Etkinlikler',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const SizedBox(height: 10),
                  if (events.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(16),
                        child: Text('Henüz etkinlik verisi yok.'),
                      ),
                    ),
                  ..._sortByDate(events)
                      .asMap()
                      .entries
                      .map((entry) => _EventCard(
                            rank: entry.key + 1,
                            event: entry.value,
                          )),
                ],
              ),
            ),
    );
  }

  List<TrafficEvent> _sortByDate(List<TrafficEvent> data) {
    final sorted = [...data]
      ..sort((a, b) => a.startTime.compareTo(b.startTime));
    return sorted.take(30).toList();
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.events});

  final List<TrafficEvent> events;

  @override
  Widget build(BuildContext context) {
    final highImpact = events.where((e) => e.trafficImpact >= 70).length;
    final categories =
        events.map((e) => e.category.toLowerCase()).toSet().length;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
          colors: [Color(0xFF1679D8), Color(0xFF40A9FF)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryColor.withAlpha(90),
            blurRadius: 18,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          _Metric(label: 'Etkinlik', value: '${events.length}'),
          const SizedBox(width: 16),
          _Metric(label: 'Kategori', value: '$categories'),
          const SizedBox(width: 16),
          _Metric(label: 'Yüksek Etki', value: '$highImpact'),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 26,
              fontWeight: FontWeight.w800,
            ),
          ),
          Text(
            label,
            style: const TextStyle(color: Colors.white70),
          ),
        ],
      ),
    );
  }
}

class _EventCard extends StatelessWidget {
  const _EventCard({required this.rank, required this.event});

  final int rank;
  final TrafficEvent event;

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.congestionColor(event.trafficImpact);
    final venue =
        (event.venue ?? '').trim().isEmpty ? 'Istanbul' : event.venue!;
    final date =
        '${event.startTime.day.toString().padLeft(2, '0')}.${event.startTime.month.toString().padLeft(2, '0')} ${event.startTime.hour.toString().padLeft(2, '0')}:${event.startTime.minute.toString().padLeft(2, '0')}';

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withAlpha(45),
          child: Text('$rank',
              style: const TextStyle(fontWeight: FontWeight.w700)),
        ),
        title: Text(event.name, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text('$venue • $date'),
        trailing: Container(
          width: 12,
          height: 38,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(999),
          ),
        ),
      ),
    );
  }
}
