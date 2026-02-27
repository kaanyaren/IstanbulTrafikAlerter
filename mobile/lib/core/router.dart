import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../screens/map_screen.dart';
import '../screens/settings_screen.dart';
import '../screens/weather_screen.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'map',
      builder: (context, state) => const MapScreen(),
    ),
    GoRoute(
      path: '/settings',
      name: 'settings',
      builder: (context, state) => const SettingsScreen(),
    ),
    GoRoute(
      path: '/weather',
      name: 'weather',
      builder: (context, state) => const WeatherScreen(),
    ),
  ],
  errorBuilder: (context, state) => Scaffold(
    body: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text('Sayfa bulunamadı: ${state.uri}'),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.go('/'),
            child: const Text('Ana Sayfaya Dön'),
          ),
        ],
      ),
    ),
  ),
);
