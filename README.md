# 🌉 Istanbul Traffic Alerter

Istanbul'un trafik yoğunluğunu gerçek zamanlı olarak takip eden, olayların trafik üzerindeki etkisini analiz eden ve yapay zeka destekli yoğunluk tahminleri sunan kapsamlı bir ekosistem.

## 🚀 Proje Hakkında

Bu proje, İstanbul sakinlerinin trafik yoğunluğunu daha iyi yönetmelerine yardımcı olmak için tasarlanmıştır. Sadece mevcut durumu göstermekle kalmaz, aynı zamanda IBB Open Data servislerinden gelen verileri işleyerek gelecekteki trafik durumunu tahmin eder.

### ✨ Temel Özellikler

- **📍 Gerçek Zamanlı Harita:** İstanbul genelindeki trafik yoğunluğu ve olayların (kaza, yol çalışması vb.) anlık takibi.
- **🔮 Tahmin Motoru:** Tarihsel veriler ve olay analizi kullanarak gelecek saatler için trafik yoğunluk skoru tahminleri.
- **⚠️ Akıllı Bildirimler:** Güzergahınız üzerindeki olaylar ve olağandışı yoğunluk artışları için anlık uyarılar.
- **📊 Etki Analizi:** Bir kazanın veya yol çalışmasının çevredeki trafiği ne ölçüde etkilediğinin analizi.
- **👤 Kişiselleştirme:** Favori güzergahlar ve kullanıcı tercihlerine göre optimize edilmiş deneyim.

## 🛠️ Teknoloji Yığını

### Backend (Python/FastAPI)

- **FastAPI:** Yüksek performanslı, asenkron API sunucusu.
- **PostgreSQL + PostGIS:** Mekansal (spatial) veriler için optimize edilmiş veritabanı.
- **Redis:** Hızlı önbellekleme ve Celery için mesaj kuyruğu.
- **Celery:** Periyodik veri çekme ve tahmin hesaplama görevleri.
- **SQLAlchemy:** Asenkron ORM.
- **Pytest:** Kapsamlı birim ve entegrasyon testleri.

### Mobile (Flutter)

- **Flutter:** Cross-platform mobil uygulama (iOS & Android).
- **Riverpod:** Modern state management.
- **Google Maps SDK:** Etkileşimli harita deneyimi.
- **Dio:** HTTP istemcisi.
- **Freezed:** İmmutable data modelleri.

## 📂 Proje Yapısı

```text
IstanbulTrafikAlerter/
├── backend/            # FastAPI tabanlı servisler ve AI motoru
├── mobile/             # Flutter mobil uygulama projesi
├── UI_Design/          # Arayüz tasarım dosyaları ve spesifikasyonlar
└── implementation_plan/# Proje fazları ve görev takibi
```

## 🏁 Başlangıç

### Backend Kurulumu

1. `backend` dizinine gidin.
2. `.env.example` dosyasını `.env` olarak kopyalayın ve gerekli bilgileri doldurun.
3. Online Supabase proje değerlerini girin:
   - `SUPABASE_URL=https://<project-ref>.supabase.co`
   - `SUPABASE_ANON_KEY=<anon-key>`
   - `SUPABASE_SERVICE_ROLE_KEY=<service-role-key>`
4. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
5. Not: Bu kurulum cloud Supabase hedefler. Yerel self-hosted kurulum gerekiyorsa `supabase/docker-compose.yml` ayrı bir opsiyon olarak kullanılabilir.

### Mobile Kurulumu

1. `mobile` dizinine gidin.
2. Bağımlılıkları çekin:
   ```bash
   flutter pub get
   ```
3. Uygulamayı Supabase değerleriyle başlatın:
   ```bash
   flutter run --dart-define=SUPABASE_URL=https://<project-ref>.supabase.co --dart-define=SUPABASE_ANON_KEY=<anon-key>
   ```

### GitHub Actions Cron (Sunucusuz Doldurma)

Bu repo, Supabase tablolarını bilgisayar açık olmadan doldurmak için üç workflow içerir:

- `.github/workflows/bootstrap-supabase.yml`: tek seferlik şema + seed + E2E kontrol
- `.github/workflows/events-cron.yml`: her 6 saatte bir etkinlik ingest
- `.github/workflows/predictions-cron.yml`: her saat başı tahmin üretimi

GitHub repository ayarlarında aşağıdaki `Secrets` değerlerini ekleyin:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL` (Supabase pooler bağlantısı, asyncpg uyumlu)
- `REDIS_URL` (opsiyonel; Actions tarafında varsayılan olarak `disabled://` kullanılır)
- `GOOGLE_MAPS_API_KEY` (opsiyonel)
- `IBB_OPEN_DATA_API_KEY` (opsiyonel)

Opsiyonel `Repository Variables`:

- `ENABLED_EVENT_CONNECTORS`
- `DISABLED_EVENT_CONNECTORS`

Workflow dosyaları `workflow_dispatch` da içerir; GitHub Actions ekranından manuel tetikleyebilirsiniz.

Önerilen ilk kurulum sırası:

1. `Bootstrap Supabase` workflow'unu manuel çalıştırın.
2. `Events Cron` workflow'unu manuel bir kez çalıştırın.
3. `Predictions Cron` workflow'unu manuel bir kez çalıştırın.
4. Sonrasında cron tetiklemeleri otomatik devam eder.

## 📄 Lisans

Bu proje MIT lisansı ile korunmaktadır. Detaylar için `LICENSE` dosyasına bakınız (yakında).

---

_Developed with ❤️ for Istanbul._
