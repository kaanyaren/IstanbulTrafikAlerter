# İstanbul Etkinlik Veri Kaynakları Raporu

Tarih: 2026-02-28
Kapsam: İstanbul'daki siyasi etkinlikler, spor etkinlikleri ve müzik etkinlikleri için sürdürülebilir veri kaynaklarının belirlenmesi.

## 1) Özet Sonuç

En doğru yaklaşım **hibrit veri toplama modeli**:

1. Önce API/RSS/kurumsal feed kaynakları,
2. Sonra parse edilebilir HTML sayfaları,
3. En son zorunluysa scraper (JS/cookie/captcha etkili kaynaklar için).

Bu sırayla gidildiğinde hem bakım maliyeti hem de kırılma riski düşer.

## 2) Önceliklendirilmiş Kaynak Listesi

Aşağıdaki liste, doğrulanabilen erişim ve sürdürülebilirlik açısından önceliklendirilmiştir.

### A. Birincil Kaynaklar (yüksek güven)

1. **İBB Kültür / Etkinlik**
   - `https://kultursanat.istanbul`
   - Projede kullanılan endpoint: `/api/event/geteventlist`
   - Güçlü yön: Şehir odaklı, resmi kaynak, mevcut sistemle uyumlu.

2. **İBB Etkinlikler (kurumsal portal)**
   - `https://www.ibb.istanbul/gundem/etkinlikler`
   - Güçlü yön: Resmi kurumsal akış, etkinlik haberleri düzenli yayınlanıyor.

3. **AKM İstanbul Etkinlikler**
   - `https://www.akmistanbul.gov.tr/tr/etkinlikler`
   - Güçlü yön: Etkinlik detay sayfaları net (başlık/tarih/kategori/link).

4. **TFF Lig/Fikstür Sayfaları (spor)**
   - `https://www.tff.org/default.aspx?pageID=198`
   - `https://www.tff.org/default.aspx?pageID=142`
   - Güçlü yön: Resmi maç/fikstür referansı.

### B. İkincil Kaynaklar (yüksek kapsama, orta operasyon maliyeti)

5. **Biletinial**
   - `https://www.biletinial.com/tr-tr`
   - Güçlü yön: Müzik + spor + sahne için geniş kapsama.
   - Risk: JS/cookie ve yapı değişiklikleri nedeniyle parser bakım ihtiyacı.

6. **Passo**
   - `https://www.passo.com.tr/tr`
   - Güçlü yön: Spor ve büyük etkinlikler için önemli kanal.
   - Risk: JS yoğunluğu ve bot korumaları nedeniyle daha maliyetli scraping.

7. **Zorlu PSM Etkinlikler**
   - `https://www.zorlupsm.com/etkinlikler`
   - Güçlü yön: Büyük ölçekli müzik/sahne etkinlikleri.
   - Risk: Cookie/JS akışı nedeniyle kontrollü scraper gerekir.

### C. Yardımcı/Fallback Kaynaklar

8. **Kulüp resmi siteleri (BJK/GS vb.)**
   - Maç duyuruları, bilet bilgileri ve branş bazlı fikstür sinyali için kullanılır.
   - Not: Galatasaray RSS feed örneği mevcut: `https://www.galatasaray.org/xml/gs.rss`

9. **İstanbul Valiliği Duyurular**
   - `https://istanbul.gov.tr/duyurular`
   - Siyasi/toplantı etkisi analizi için yardımcı sinyal kaynağı.

10. **İBB Duyurular**

- `https://www.ibb.istanbul/gundem/duyurular`
- Yol kapanışı, toplu etkinlik, kamusal duyuru etkileri için yardımcı sinyal.

## 3) Siyasi Etkinlik Verisi için Gerçekçi Strateji

Parti il/ilçe sitelerinde her zaman stabil API/RSS bulunmuyor. Bu yüzden:

- Birincil: Valilik + belediye + resmi kurum duyuruları
- İkincil: Parti/organizasyon resmi web sayfaları
- Üçüncül: Resmi sosyal medya hesaplarından yapılandırılmış sinyal (linkli duyuru)

Bu kademeli yaklaşım, siyasi veri tarafındaki kırılganlığı azaltır.

## 4) Toplama Mimarisi (Öneri)

### Kaynak türüne göre connector

- `api_connector`
- `rss_connector`
- `html_connector`
- `dynamic_scraper_connector` (yalnızca zorunlu kaynaklarda)

### Zorunlu normalize alanlar

- `title`
- `start_time`
- `end_time` (varsa)
- `venue`
- `district`
- `lat`
- `lon`
- `category` (sport/music/political/other)
- `source`
- `source_id`
- `url`
- `last_seen_at`

### Dedupe

- Birincil anahtar: `source + source_id`
- Fallback: `hash(normalized_title + date + venue)`

## 5) Çalıştırma Sıklığı (Cron Önerisi)

Başlangıç için:

- **Günde 4 kez**: 06:00, 11:00, 16:00, 21:00

Yoğun dönemlerde (derbi, büyük konser haftası, resmi miting takvimleri):

- Ek 1-2 tarama penceresi (ör. 14:00 ve 19:00)

## 6) Operasyonel Kurallar

- API/RSS varsa scraper çalıştırma.
- robots.txt ve kullanım koşullarına uy.
- İstek hızını sınırla (rate limit).
- `If-Modified-Since` / `ETag` destekleniyorsa kullan.
- Kaynak bazlı hata izolasyonu yap (bir kaynağın çökmesi tüm pipeline'ı durdurmasın).
- Parser hatası, boş veri oranı ve ani hacim düşüşü için alarm üret.

## 7) Proje ile Uyum Notu

Mevcut backend yapısında event toplama ve periyodik görev altyapısı zaten var:

- Event adapter yaklaşımı mevcut,
- Celery periyodik görevleri mevcut,
- Redis cache/broker mevcut.

Bu nedenle önerilen model, mevcut mimariye doğrudan genişletme şeklinde uygulanabilir.

## 8) Uygulama Önceliği (Kısa Yol Haritası)

1. İBB Kültür + İBB Etkinlik + TFF + AKM connector'larını stabilize et.
2. Biletinial ve Zorlu PSM için kontrollü HTML parser ekle.
3. Passo için sadece gerekli alanlara odaklı, düşük frekanslı connector başlat.
4. Siyasi sinyal katmanını (Valilik + İBB duyurular + parti siteleri fallback) devreye al.
5. Veri kalite dashboard'u (kaynak bazlı başarı/hata/yenilik sayısı) ekle.

---

Bu rapor, veri kapsama ile operasyon maliyeti arasında dengeli bir kaynak stratejisi sunar ve mevcut proje mimarisiyle uyumludur.

## 9) İlgili Doküman

- Uygulanabilir connector iş planı: `connector_backlog.md`
