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
   * **GFS Global** (28/13 km çözünürlük)
   * **Météo-France Seamless** (2 km çözünürlük)
   * **GEM Seamless** (Kanada 25/10/2.5 km çözünürlük)
   * **UKMO Seamless** (Birleşik Krallık / Küresel 10/2 km çözünürlük)

4. **Multi-Model Kurulum Desteği:** Aynı bölge (Zone) için farklı tahmin modellerine ait birden fazla entegrasyon kurabilir, böylece arayüzde modelleri yan yana kıyaslayabilirsiniz.

---

## 🛠️ Kurulum Kılavuzu

Entegrasyonu Home Assistant sisteminize yüklemek için aşağıdaki yöntemlerden birini seçebilirsiniz.

### Yöntem A: HACS ile Kurulum (En Kolay & Önerilen)

Eğer sisteminizde HACS (Home Assistant Community Store) kuruluysa, güncellemeleri kolayca takip edebilmek için bu yöntemi tercih edin:

1. Home Assistant sol menüsünden **HACS** arayüzünü açın.
2. Sağ üst köşedeki **üç noktaya** tıklayın ve **Custom repositories (Özel depolar)** seçeneğini seçin.
3. Açılan pencerede:
   * **Repository (Depo):** `https://github.com/iosmand/ha-open-meteo-custom`
   * **Category (Kategori):** `Integration` (Entegrasyon) seçin.
   * **Add (Ekle)** butonuna tıklayın.
4. Listeye eklenen **Open-Meteo Custom** entegrasyonuna tıklayın ve sağ alttaki **Download (İndir)** butonuna basarak indirin.
5. Home Assistant'ı yeniden başlatın (**Geliştirici Araçları > YAML > Yeniden Başlat**).

---

### Yöntem B: Manuel Kurulum (Standart HA İşletim Sistemleri)

Sisteminizde terminal/SSH erişimi veya dosya yöneticisi (File Editor/Samba) varsa:

1. Bu depodaki `custom_components/open_meteo_custom` klasörünü bilgisayarınıza indirin.
2. Home Assistant `/config/` dizininin altında `custom_components` adında bir klasör yoksa oluşturun.
3. İndirdiğiniz `open_meteo_custom` klasörünü bu `custom_components` klasörünün içine kopyalayın. Klasör yapınız aşağıdaki gibi olmalıdır:
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
4. Home Assistant'ı yeniden başlatın.

---

### Yöntem C: Docker Container Üzerinde Kurulum

Eğer Home Assistant'ı bir Docker konteyneri olarak (örn. Synology NAS, Unraid veya bağımsız Linux docker) çalıştırıyorsanız:

#### Seçenek 1: Volume Map (Bağlama) Üzerinden Kopyalama (Önerilen)
Home Assistant konteynerini kurarken muhtemelen host makinenizde bir klasörü `/config` dizinine bağladınız (Örn: `-v /home/user/homeassistant:/config`).
1. Host makinenizdeki bu konuma gidin: `/home/user/homeassistant/` (kendi yolunuza göre güncelleyin).
2. Burada `custom_components` klasörünü bulun (yoksa oluşturun) ve içine `open_meteo_custom` klasörünü yerleştirin.
3. Konteyneri yeniden başlatın:
   ```bash
   docker restart <container_name_or_id>
   ```

#### Seçenek 2: `docker cp` Komutu ile Kopyalama
Eğer host makinede dosyayı bağladığınız klasörü bulamıyorsanız, dosyaları doğrudan konteynerin içine kopyalayabilirsiniz:
1. Depoyu host makinenize indirin ve terminalde o klasöre gidin.
2. Klasörü doğrudan çalışan konteynerin içine kopyalamak için şu komutu çalıştırın (kendi konteyner adınızı yazın):
   ```bash
   docker cp custom_components/open_meteo_custom <homeassistant_container_name>:/config/custom_components/
   ```
3. Konteyner içindeki izinleri kontrol etmek ve temizlemek için konteyneri yeniden başlatın:
   ```bash
   docker restart <homeassistant_container_name>
   ```

---

## ⚙️ Entegrasyonun Etkinleştirilmesi

Kurulum yöntemlerinden biriyle dosyaları yükleyip sistemi yeniden başlattıktan sonra:

1. **Ayarlar > Cihazlar ve Hizmetler > Entegrasyon Ekle** adımlarını izleyin.
2. Arama kutusuna **"Open-Meteo Custom"** yazın ve seçin.
3. Karşınıza gelen kurulum penceresinde:
   * **Bölge (Zone):** Hava verilerini çekmek istediğiniz konumu (örneğin eviniz/Home zone) seçin.
   * **Tahmin Modeli:** Kullanmak istediğiniz tahmin modelini seçin (Türkiye için **DWD ICON Europe (7 km)** en isabetli sonuçları verir).
4. **Gönder** butonuna tıklayarak kurulumu tamamlayın. Varlıklar ve sensörler saniyeler içinde Home Assistant sisteminizde görünecektir.
