# Faz 5: Flutter Mobil Uygulama

---

## Görev 5.1 — Flutter Proje İskeleti
- **Girdi:** Yok
- **Çıktı:** `mobile/` klasörü
- **Talimat:** `flutter create istanbul_traffic_alerter` ile proje oluştur. Bağımlılıklar: `google_maps_flutter`, `dio`, `riverpod`, `go_router`, `freezed`, `json_serializable`, `geolocator`, `flutter_local_notifications`. Temel klasör yapısı: `lib/screens/`, `lib/services/`, `lib/models/`, `lib/providers/`, `lib/widgets/`.
- **Doğrulama:** `flutter run` ile boş uygulama emülatörde açılmalı.

---

## Görev 5.2 — API Servis Katmanı (Dio)
- **Girdi:** Görev 5.1, 4.1
- **Çıktı:** `mobile/lib/services/api_service.dart`
- **Talimat:** Dio ile HTTP client: base URL konfigürasyonu, JWT token interceptor (token'ı SecureStorage'da sakla), error handling, retry interceptor. Metodlar: `login()`, `getEvents()`, `getPredictions(lat, lon, radius)`, `getPredictionTimeSeries(zoneId)`.
- **Doğrulama:** Backend'e istek atıp response alabilme testi.

---

## Görev 5.3 — Harita Ekranı (Ana Ekran)
- **Girdi:** Görev 5.1, 5.2
- **Çıktı:** `mobile/lib/screens/map_screen.dart`
- **Talimat:** Google Maps widget: İstanbul merkezli başlangıç. Kullanıcı konumunu göster. Yakınlaştırma/uzaklaştırma. Kamera pozisyonu değiştiğinde (idle) ekranda görünen bölge için tahmin verilerini çek.
- **Doğrulama:** Emülatörde harita görüntülenmeli, konum gösterilmeli.

---

## Görev 5.4 — Congestion Heatmap Overlay
- **Girdi:** Görev 5.3
- **Çıktı:** `mobile/lib/widgets/congestion_overlay.dart`
- **Talimat:** Tahmin verilerini harita üzerinde renk kodlu overlay olarak göster. Renk skalası: Yeşil (0-30) → Sarı (31-60) → Turuncu (61-80) → Kırmızı (81-100). Yarı-saydam poligonlar (bölge sınırları) veya daireler (koordinat merkezli). Dinamik güncelleme (veri değiştiğinde animasyonlu geçiş).
- **Doğrulama:** Harita üzerinde farklı renklerde trafik yoğunluk alanları görünmeli.

---

## Görev 5.5 — Etkinlik Marker'ları & Detay Bottom Sheet
- **Girdi:** Görev 5.3, 5.2
- **Çıktı:** `mobile/lib/widgets/event_marker.dart` + `mobile/lib/widgets/event_detail_sheet.dart`
- **Talimat:** Her etkinlik için haritada özel marker (kategori ikonlu). Marker'a tıklanınca bottom sheet açılsın: etkinlik adı, tarih/saat, mekan, tahmini trafik etkisi, kapasite. Bottom sheet sürüklenebilir olsun.
- **Doğrulama:** Marker tıklama → bottom sheet açılması akışı çalışmalı.

---

## Görev 5.6 — Bildirim Sistemi
- **Girdi:** Görev 5.1
- **Çıktı:** `mobile/lib/services/notification_service.dart`
- **Talimat:** `flutter_local_notifications` ile lokal bildirim. Kullanıcının seçtiği bölgeler için tahmin skoru eşik değerini aşınca bildirim gönder. Arka planda çalışan periyodik kontrol (WorkManager veya background fetch). Bildirim içeriği: "⚠️ Kadıköy bölgesinde yarın 18:00'de yüksek trafik bekleniyor (Skor: 85/100)".
- **Doğrulama:** Test bildirimi tetiklenebilmeli.

---

## Görev 5.7 — Ayarlar Ekranı
- **Girdi:** Görev 5.1
- **Çıktı:** `mobile/lib/screens/settings_screen.dart`
- **Talimat:** Kullanıcı tercihleri: bildirim açık/kapalı, bildirim eşik skoru (slider, 50-100), takip edilen bölgeler (multi-select), tema (aydınlık/karanlık), dil seçimi. SharedPreferences ile kaydet.
- **Doğrulama:** Ayarlar kaydedilip uygulama yeniden açıldığında korunmalı.
