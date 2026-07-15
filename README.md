# Open-Meteo Custom Integration for Home Assistant

Bu özel entegrasyon (custom integration), Home Assistant'ın varsayılan Open-Meteo entegrasyonundaki tüm veri kısıtlamalarını giderir. Open-Meteo API'sinin desteklediği en detaylı hava durumu verilerini çeker ve kullanıcının arayüzden dilediği hava tahmin modelini (örn. DWD ICON Europe, ECMWF, GFS) seçmesine olanak tanır.

---

## ✨ Özellikler

1. **Gelişmiş Weather Entity:** Standart hava durumu kartına ek olarak aşağıdaki verileri anlık öznitelik (attributes) olarak sisteme ekler:
   * Bağıl Nem (`humidity`)
   * Hava Basıncı (`native_pressure`)
   * Hissedilen Sıcaklık (`native_apparent_temperature`)
   * Çiy Noktası (`native_dew_point`)
   * Bulutluluk Oranı (`cloud_coverage`)
   * Rüzgar Hamlesi Hızı (`native_wind_gust_speed`)
   * *Ayrıca saatlik ve günlük tahmin veri setleri de nem, basınç, bulutluluk gibi tüm bu yeni nitelikleri içerecek şekilde genişletilmiştir.*

2. **Bağımsız Sensörler (Platform: Sensor):** Verileri otomasyonlarda doğrudan kullanabilmeniz ve grafik çizebilmeniz için bağımsız sensörler oluşturulur:
   * `sensor.[bölge]_humidity` (Nem - %)
   * `sensor.[bölge]_pressure` (Basınç - hPa)
   * `sensor.[bölge]_apparent_temperature` (Hissedilen Sıcaklık - °C)
   * `sensor.[bölge]_dew_point` (Çiy Noktası - °C)
   * `sensor.[bölge]_cloud_cover` (Bulut Oranı - %)
   * `sensor.[bölge]_wind_gust` (Rüzgar Hamlesi - km/h)

3. **Gelişmiş Model Seçimi:** Arayüz kurulum ekranında Open-Meteo'nun en iyi tahmin modelini otomatik seçen `best_match` varsayılan ayarının yanı sıra aşağıdaki modelleri el ile seçebilirsiniz:
   * **DWD ICON Europe** (7 km çözünürlük - Türkiye için en isabetlisi)
   * **DWD ICON Global** (13 km çözünürlük)
   * **ECMWF IFS** (Dünya geneli 25/9 km çözünürlük)
   * **GFS Global**
   * **Météo-France Seamless**
   * **GEM Seamless**
   * **UKMO Global**

4. **Multi-Model Kurulum Desteği:** Aynı bölge (Zone) için farklı tahmin modellerine ait birden fazla entegrasyon kurabilir, böylece arayüzde modelleri yan yana kıyaslayabilirsiniz.

---

## 🛠️ Kurulum Adımları

Entegrasyonu Home Assistant sisteminize yüklemek için şu adımları takip edin:

1. **Dosyaları Kopyalayın:**
   `/home/i0s/Documents/ha-open-meteo-custom/custom_components/open_meteo_custom/` klasörünü Home Assistant kurulumunuzun `/config/custom_components/` dizini altına kopyalayın. Klasör yapısı şu şekilde olmalıdır:
   ```text
   config/
   └── custom_components/
       └── open_meteo_custom/
           ├── __init__.py
           ├── const.py
           ├── config_flow.py
           ├── coordinator.py
           ├── weather.py
           ├── sensor.py
           ├── manifest.json
           └── translations/
               ├── en.json
               └── tr.json
   ```

2. **Home Assistant'ı Yeniden Başlatın:**
   Dosyaları kopyaladıktan sonra Home Assistant arayüzünden **Geliştirici Araçları > YAML > Yeniden Başlat** altından sistemi yeniden başlatın.

3. **Cihaz Ekleme:**
   * **Ayarlar > Cihazlar ve Hizmetler > Entegrasyon Ekle** adımlarını izleyin.
   * Arama kutusuna **"Open-Meteo Custom"** yazın.
   * Karşınıza gelen pencerede hava verilerini çekmek istediğiniz **Bölgeyi (Zone)** ve kullanmak istediğiniz **Tahmin Modelini** seçip kurulumu tamamlayın.
