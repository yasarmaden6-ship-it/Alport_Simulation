# Alport_Simulation

IE401 bitirme projesi için SimPy ile hazırlanmış basit bir liman simülasyonu. Gemi gelişlerini, rıhtım kuyruğunu ve yağmur nedeniyle duran operasyonları gösterir.

## Kurulum ve çalıştırma

Bu klasörde terminal açıp çalıştır:

```bash
python3 -m pip install -r requirements.txt
python3 baby_simulation.py
```

Python 3.13 ve SimPy 4.1.2 ile kontrol edildi.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `baby_simulation.py` | Ortamı ve ortak yağmur takvimini hazırlar, modeli çalıştırır |
| `ayarlar.py` | Rıhtım sayısını, süreleri ve olasılıkları tutar |
| `gelisler.py` | Saatlik gemi gelişlerini oluşturur |
| `liman.py` | Geminin kuyruğunu, operasyonunu ve ayrılışını yönetir |
| `sonuclar.py` | Gemi sayılarını ve süreleri ekrana yazdırır |

## Modelin kuralları

- Üç rıhtım vardır; her rıhtım aynı anda bir gemi alır
- Tek gemi tipi kullanılır; her gemi 100 saat net çalışma gerektirir
- Her saat ayrı Uniform(0,1) çekilişleriyle yağmur ve gemi gelişi belirlenir
- Saatlik gemi geliş olasılığı 0.01575, yağmur olasılığı 0.329'dur
- Saatte en fazla bir gemi gelir; ilk gelen gemi önce hizmet alır
- Yağmur bütün liman için ortaktır; gemiler rıhtımlarını tutar, işleri ilerlemez
- Hava açılınca kalan işten devam edilir
- Liman başlangıçta boştur; gözlem aralığı `0 <= saat < 720` olarak alınır
- `SEED = 42`, aynı ayarlarla aynı rastgele senaryoyu tekrar üretir

Model veri dosyası okumadan `ayarlar.py` içindeki değerlerle çalışır. Olasılıklar ve çalışma kuralları bu örnek modelin varsayımlarıdır.

## Sonuçlar

Program gelen, ayrılan, kuyrukta kalan ve rıhtımda kalan gemi sayılarını yazdırır. Ortalama kuyruk süresi yanaşan gemilerden, ortalama limanda kalış süresi ayrılan gemilerden hesaplanır. Ayrılan gemilerin yağmur beklemeleri ayrıca gösterilir.

Varsayılan ayarlarla kontrol edilen örnek çalışmada 8 gemi gelir, 7 gemi ayrılır ve 1 gemi rıhtımda kalır. Ortalama kuyruk süresi 2.62 saat, ayrılan gemilerin ortalama limanda kalışı 153 saattir.
