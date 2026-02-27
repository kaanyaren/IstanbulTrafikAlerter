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
3. Docker Compose ile servisleri başlatın:
   ```bash
   docker-compose up -d
   ```
4. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

### Mobile Kurulumu
1. `mobile` dizinine gidin.
2. Bağımlılıkları çekin:
   ```bash
   flutter pub get
   ```
3. Uygulamayı başlatın:
   ```bash
   flutter run
   ```

## 📄 Lisans

Bu proje MIT lisansı ile korunmaktadır. Detaylar için `LICENSE` dosyasına bakınız (yakında).

---
*Developed with ❤️ for Istanbul.*
