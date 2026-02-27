import 'package:dio/dio.dart';
import '../core/constants.dart';
import '../models/prediction.dart';
import '../models/event.dart';
import 'storage_service.dart';

class ApiService {
  static ApiService? _instance;
  late final Dio _dio;

  ApiService._() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: AppConstants.connectTimeout,
      receiveTimeout: AppConstants.receiveTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(_AuthInterceptor());
    _dio.interceptors.add(_RetryInterceptor(_dio));
    _dio.interceptors.add(LogInterceptor(
      requestBody: false,
      responseBody: false,
      logPrint: (obj) => debugLog(obj.toString()),
    ));
  }

  static ApiService get instance {
    _instance ??= ApiService._();
    return _instance!;
  }

  void debugLog(String msg) {
    // ignore: avoid_print
    print('[ApiService] $msg');
  }

  // ── Auth ─────────────────────────────────────────────────────────────────

  Future<String?> login(String email, String password) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'username': email,
        'password': password,
      });
      final token = response.data['access_token'] as String?;
      if (token != null) {
        await StorageService.saveToken(token);
      }
      return token;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // ── Events ────────────────────────────────────────────────────────────────

  Future<List<TrafficEvent>> getEvents({
    DateTime? startDate,
    DateTime? endDate,
    String? category,
    double? lat,
    double? lon,
    double? radiusKm,
  }) async {
    // Return mock data if backend not available
    try {
      final params = <String, dynamic>{};
      if (startDate != null) params['start_date'] = startDate.toIso8601String();
      if (endDate != null) params['end_date'] = endDate.toIso8601String();
      if (category != null) params['category'] = category;
      if (lat != null) params['lat'] = lat;
      if (lon != null) params['lon'] = lon;
      if (radiusKm != null) params['radius_km'] = radiusKm;

      final response = await _dio.get(
        '/api/v1/events',
        queryParameters: params,
      );
      final list = response.data as List<dynamic>;
      return list.map((e) => TrafficEvent.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout) {
        // Return mock data when backend unavailable
        return TrafficEvent.mockData();
      }
      throw _handleError(e);
    }
  }

  // ── Predictions ───────────────────────────────────────────────────────────

  Future<List<Prediction>> getPredictions(double lat, double lon, double radiusKm) async {
    try {
      final response = await _dio.get(
        '/api/v1/predictions',
        queryParameters: {'lat': lat, 'lon': lon, 'radius_km': radiusKm},
      );
      final list = response.data as List<dynamic>;
      return list.map((e) => Prediction.fromJson(e as Map<String, dynamic>)).toList();
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout) {
        return Prediction.mockData();
      }
      throw _handleError(e);
    }
  }

  Future<Map<String, dynamic>> getPredictionTimeSeries(int zoneId) async {
    try {
      final response = await _dio.get('/api/v1/predictions/$zoneId/series');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
        return Exception('Bağlantı zaman aşımına uğradı.');
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        if (statusCode == 401) return Exception('Oturum süresi doldu. Lütfen tekrar giriş yapın.');
        if (statusCode == 403) return Exception('Bu işlem için yetkiniz yok.');
        if (statusCode == 404) return Exception('İstenen kaynak bulunamadı.');
        return Exception('Sunucu hatası: $statusCode');
      case DioExceptionType.connectionError:
        return Exception('İnternet bağlantısı yok.');
      default:
        return Exception('Bilinmeyen hata: ${e.message}');
    }
  }
}

// ── Interceptors ──────────────────────────────────────────────────────────────

class _AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await StorageService.getToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    return handler.next(options);
  }
}

class _RetryInterceptor extends Interceptor {
  final Dio dio;
  static const int _maxRetries = AppConstants.maxRetries;

  _RetryInterceptor(this.dio);

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final extra = err.requestOptions.extra;
    final retryCount = (extra['retryCount'] as int?) ?? 0;

    final shouldRetry = retryCount < _maxRetries &&
        (err.type == DioExceptionType.connectionTimeout ||
            err.type == DioExceptionType.receiveTimeout ||
            (err.response?.statusCode != null &&
                err.response!.statusCode! >= 500));

    if (shouldRetry) {
      await Future.delayed(Duration(milliseconds: 500 * (retryCount + 1)));
      err.requestOptions.extra['retryCount'] = retryCount + 1;
      try {
        final response = await dio.request(
          err.requestOptions.path,
          options: Options(
            method: err.requestOptions.method,
            headers: err.requestOptions.headers,
            extra: err.requestOptions.extra,
          ),
          data: err.requestOptions.data,
          queryParameters: err.requestOptions.queryParameters,
        );
        return handler.resolve(response);
      } catch (e) {
        return handler.next(err);
      }
    }
    return handler.next(err);
  }
}
