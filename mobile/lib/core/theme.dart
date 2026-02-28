import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  static const _primaryColor = Color(0xFF2196F3);
  static const _secondaryColor = Color(0xFF1CC8A0);
  static const _errorColor = Color(0xFFFF5A5F);
  static const _warningColor = Color(0xFFFFB020);
  static const _surfaceDark = Color(0xFF0A1628);
  static const _surfaceDarkElevated = Color(0xFF152238);
  static const _surfaceLight = Color(0xFFF6F9FF);

  static ThemeData lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: const ColorScheme(
      brightness: Brightness.light,
      primary: _primaryColor,
      onPrimary: Colors.white,
      secondary: _secondaryColor,
      onSecondary: Colors.white,
      error: _errorColor,
      onError: Colors.white,
      surface: _surfaceLight,
      onSurface: Color(0xFF0B1A2B),
    ),
    scaffoldBackgroundColor: const Color(0xFFEFF4FF),
    textTheme: GoogleFonts.interTextTheme().apply(
      bodyColor: const Color(0xFF0B1A2B),
      displayColor: const Color(0xFF0B1A2B),
    ),
    appBarTheme: const AppBarTheme(
      elevation: 0,
      centerTitle: false,
      backgroundColor: Colors.transparent,
      foregroundColor: Color(0xFF0B1A2B),
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: _primaryColor,
      foregroundColor: Colors.white,
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      shadowColor: const Color(0xFF0F6BBA).withAlpha(35),
    ),
    chipTheme: const ChipThemeData(
      shape: StadiumBorder(),
      side: BorderSide(color: Color(0x552196F3)),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: _primaryColor,
      unselectedItemColor: Color(0xFF8A98AD),
      backgroundColor: Colors.white,
      type: BottomNavigationBarType.fixed,
      elevation: 0,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Colors.white,
      indicatorColor: const Color(0x332196F3),
      labelTextStyle: WidgetStateProperty.all(
        const TextStyle(fontWeight: FontWeight.w600),
      ),
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const IconThemeData(color: _primaryColor);
        }
        return const IconThemeData(color: Color(0xFF8A98AD));
      }),
    ),
  );

  static ThemeData darkTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    colorScheme: const ColorScheme(
      brightness: Brightness.dark,
      primary: _primaryColor,
      onPrimary: Colors.white,
      secondary: _secondaryColor,
      onSecondary: Colors.white,
      error: _errorColor,
      onError: Colors.white,
      surface: _surfaceDark,
      onSurface: Colors.white,
    ),
    scaffoldBackgroundColor: _surfaceDark,
    textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
    appBarTheme: const AppBarTheme(
      elevation: 0,
      centerTitle: false,
      backgroundColor: Colors.transparent,
      foregroundColor: Colors.white,
    ),
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: _primaryColor,
      foregroundColor: Colors.white,
    ),
    cardTheme: CardThemeData(
      elevation: 0,
      color: _surfaceDarkElevated,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      shadowColor: Colors.black.withAlpha(80),
    ),
    chipTheme: const ChipThemeData(
      shape: StadiumBorder(),
      side: BorderSide(color: Color(0x884CA8FF)),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      selectedItemColor: Color(0xFF75C6FF),
      unselectedItemColor: Color(0xFF73839A),
      backgroundColor: _surfaceDarkElevated,
      type: BottomNavigationBarType.fixed,
      elevation: 0,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: _surfaceDarkElevated,
      indicatorColor: const Color(0x334CB6FF),
      labelTextStyle: WidgetStateProperty.all(
        const TextStyle(fontWeight: FontWeight.w600),
      ),
      iconTheme: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) {
          return const IconThemeData(color: Color(0xFF75C6FF));
        }
        return const IconThemeData(color: Color(0xFF73839A));
      }),
    ),
  );

  // Traffic congestion colors
  static Color congestionColor(int score) {
    if (score <= 30) return const Color(0xFF34A853); // Green
    if (score <= 60) return const Color(0xFFFBBC05); // Yellow
    if (score <= 80) return const Color(0xFFFF6D00); // Orange
    return const Color(0xFFEA4335); // Red
  }

  static Color get primaryColor => _primaryColor;
  static Color get secondaryColor => _secondaryColor;
  static Color get errorColor => _errorColor;
  static Color get warningColor => _warningColor;
  static Color get surfaceDark => _surfaceDark;
  static Color get surfaceDarkElevated => _surfaceDarkElevated;
}
