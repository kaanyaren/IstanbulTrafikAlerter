# Istanbul Traffic Alerter (Mobile)

## Çalıştırma

1. Bağımlılıkları kurun:
   - `flutter pub get`
2. Uygulamayı cloud Supabase ile başlatın:
   - `flutter run --dart-define=SUPABASE_URL=https://<project-ref>.supabase.co --dart-define=SUPABASE_ANON_KEY=<anon-key>`

## Notlar

- `SUPABASE_URL` ve `SUPABASE_ANON_KEY` zorunludur.
- Bu değerler verilmeden uygulama başlatılırsa `StateError` ile durdurulur.
