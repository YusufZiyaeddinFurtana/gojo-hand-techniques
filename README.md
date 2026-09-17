# Limitless — Gojo el teknikleri

Yerel Python/OpenCV kamera uygulaması. **Sağ el kırmızı, sol el mavi; birleşince mor.** Kameranın üzerinde yazı, başlık, yardım paneli veya FPS göstergesi yok. Efektler verilen anime referanslarından esinlenerek kodla çizilir.

## macOS ve Windows sürümleri

| Platform | Başlatıcı | Gereksinim | Rehber |
| --- | --- | --- | --- |
| macOS | **Baslat.command** | Apple Silicon, macOS 13+, Python 3.12–3.14 | [macOS kurulumu](docs/MACOS.md) |
| Windows | **Baslat.bat** | Windows 10/11 x64, Python 3.12–3.14 (64-bit) | [Windows kurulumu](docs/WINDOWS.md) |

**Code → Download ZIP** ile indir, klasöre çıkar, platformuna ait başlatıcıya çift tıkla. Önerilen Python: **3.12**. İlk açılış paketleri ve modelleri indirir; sonra yerelde çalışır. Açık eski sürümü önce `Q` ile kapat. Bunlar Python kaynak sürümleridir; bağımsız `.app` / `.exe` paketleri değildir.

Ayrı platform ZIP'leri üretmek için `python scripts/package.py` kullan. Çıktılar `dist/gojo-hand-techniques-macos.zip` ve `dist/gojo-hand-techniques-windows.zip` olur. Hazır paketler repo **Releases** bölümünde sunulur.

## Çağırma ve birleştirme

| Teknik | Hareket | Görsel davranış |
| --- | --- | --- |
| Kırmızı | **Sağ elde işaret ve orta parmak yan yana uzatılmış**, yüzük ve serçe kapalı; yaklaşık 0,4 saniye tut. | Büyük kızıl çekirdek, dışarı savrulan parçacıklar ve genişleyen basınç halkaları. |
| Mavi | **Sol el açık, avuç içi tavana bakacak şekilde**; yaklaşık 0,4 saniye tut. Bir top taşıyormuş gibi, avucu kameraya hafifçe eğebilirsin. | Avucun üzerinde büyük mavi çekirdek; çevreden kıvrılarak içine çekilen parçacıklar. |
| Mor | İki enerji de elindeyken küreleri yaklaştır ve yaklaşık 0,4 saniye birlikte tut. | Kırmızı/mavi birbirinin etrafında dönerek birleşir; mor sağ ele geçer. |

Enerji oluştuktan sonra çağırma hareketini bırakabilirsin. Maviyi çağırdıktan sonra atış tutuşunun görünmesi için avucunu kameraya çevirebilirsin. İki eli tamamen üst üste bindirmek yerine yan yana yaklaştır.

## Alan genişletme — Sonsuz Boşluk

**Tek elinde işaret ve orta parmağını çaprazla; yüzük ve serçeyi kapat. Kameraya göstererek yaklaşık 0,55 saniye tut.** Sağ veya sol el çalışır. İki parmağın yalnızca yan yana durması veya uçlarının değmesi yeterli değildir; çaprazlama kameradan seçilmelidir.

Algılama, uçların yer değiştirmesine ek olarak parmak eklemleri arasındaki çizgilerin kesişmesini de kabul eder; bir parmağın hafif bükülmesi sorun değildir. Görünen elde 0,14 saniyeye kadar kısa sınıflandırma titremeleri hazırlığı hemen sıfırlamaz. El tamamen kaybolursa birikim sıfırlanır; yan yana iki parmak ve yalnızca değen uçlar alan açmaz.

Alan açılınca oda arka planı **12 saniyeliğine** karanlık bir uzaya dönüşür: parlak beyaz/mavi boşluk halkası, hareketli bulutlar ve dışarı akan yıldız izleri. İnsan ayırma modeli seni ön planda tutmaya çalışır. **İrislerin parlak mavi/camgöbeği olur**; yüz hareketi ve göz kırpma takip edilir, göz bebeği korunur. Göz rengi alanla beraber açılıp kapanır. Yüz görülmediğinde önceki konuma efekt çizilmez. Açılış ve kapanış yumuşak geçişlidir; elini indirsen de süre tamamlanır. Yazı gösterilmez.

Tekrar açmak için etki bittikten sonra parmaklarını ayırıp yeniden çaprazla. Aynı pozu tutmak süreyi uzatmaz veya otomatik tekrar açmaz. `R` alanı da anında sıfırlar. Diğer enerji teknikleri kullanılmaya devam edebilir; çapraz tutuş sırasında atış hazırlığı iptal edilir.

Bu görünüm, [7. bölümdeki Unlimited Void sahnesinden](https://otakuorbit.com/jujutsu-kaisen-episode-7-recap-and-review/) esinlenen özgün bir prosedürel efekttir. Anime karesi veya video kesiti kullanılmaz. Arka plan ayırma yaklaşık 250 KB, göz takibi yaklaşık 4 MB ek model indirir. Göz modeli yüklenemezse terminalde uyarı verilir; diğer efektler çalışır. `--no-eye-glow` göz modelini kapatır. Model yüklenemezse uygulama kapanmaz; kamera saydam biçimde uzay görüntüsüne karıştırılır. Saç ve hızlı hareket eden parmakların çevresinde maske hataları olabilir.

## Üç rengi de fırlatma

Her renk aynı hazırlık sırasını kullanır:

1. Enerji oluştuktan sonra yaklaşık **bir saniye bekle**. Başparmak ve kullanacağın parmağın uçlarını kısa süre **ayrık** tut.
2. Başparmak ucunu **işaret veya orta parmak ucuna hafifçe değdirip yaklaşık 0,3 saniye tut**. İşaret parmağıyla yapılan “OK” tutuşu da desteklenir; parmakları üst üste bastırmak gerekmez.
3. Kürenin çevresinde **parlak beyaz bir halka** belirince atış hazırdır.
4. Tutuşu yaptığın parmağı başparmaktan **hızlıca ayır**. Gerçek şıklatma sesi gerekmez; kameranın parmakların ayrıldığını görmesi gerekir. Bırakış mesafesi, hazırlık sırasında ölçülen hafif temasa göre ayarlanır. İşaret ve orta parmak ayrı izlenir; diğer parmağın hareketi tutulan teması bırakmış sayılmaz.

- **Kırmızı:** İşaret parmağının görüntüde gösterdiği yönde düz fırlar; diğer eldeki mavi korunur.
- **Mavi:** Elinden ayrılır ve yaklaşık **5 saniye etrafında genişleyip daralan bir spiral** çizerek dolaşır. Çevresindeki parçacıkları çekmeye devam eder.
- **Mor:** Kameraya doğru büyüyerek fırlar, enerji çizgileri ve şok dalgası oluşturur.

Sıradan el hareketleri veya kameraya yaklaşmak artık atış tetiklemez. Eski açık avuçla itme alternatifi kaldırıldı. Tek karelik parmak açılması yeterli değildir; en az iki karede doğrulanır. Yavaşça açmak hazırlığı iptal eder. Takip kaybı, büyük konum sıçraması, düşük sağ/sol güveni veya uzun kare gecikmesi de hazırlığı iptal eder. Bu durumda parmakları ayırıp tutuşu yeniden yap. Hazır tutuş 3 saniye sonra iptal olur.

Bir rengi attıktan sonra yeniden çağırmak için önce çağırma pozundan çıkıp tekrar yap. Açık avucu sabit tutmak arka arkaya mavi üretmez. Mor atıldıktan sonra kısa bir yenilenme süresi vardır.

## Tuşlar

| Tuş | İşlev |
| --- | --- |
| `Q` / `Esc` | Çık |
| `R` | Bütün enerjileri ve atışları sıfırla |
| `D` | Yalnızca el takip noktalarını aç/kapat; yazı göstermez |
| `S` | Sağ/sol renk eşlemesini değiştir ve sıfırla |
| `L` | Daha az parçacıklı hafif efekt modu |

Görüntü ayna gibi çevrilir. Gerçek sağ elinde mavi oluşuyorsa `S` ile eşlemeyi değiştir.

## Demo, kayıt ve kurulum

**18 saniyelik sentetik efekt demosu** aşağıdaki komutla üretilebilir; video dosyaları repoya dahil değildir. Sırasıyla iki renk, kırmızı atışı, mavi spirali, birleşme ve mor atışı gösterir. El konumları simüle edilir; gerçek bir kişide takip doğruluğunun kanıtı değildir. Kullanıcının isteğine uygun olarak videonun üstünde de yazı yoktur.

```sh
# Kamera/model gerektirmeyen demo
.venv/bin/python main.py --demo

# Sonsuz Boşluk demosu: sentetik tetikleme, 12 saniyelik alan ve normale dönüş
.venv/bin/python main.py --demo-domain
.venv/bin/python main.py --demo-domain --headless --record output/domain-demo.mp4 --preview-dir output/domain-preview

# Farklı kamera veya daha düşük yük
.venv/bin/python main.py --camera 1
.venv/bin/python main.py --width 960 --height 540 --reduced-effects

# İsteğe bağlı kamera kaydı
.venv/bin/python main.py --record output/kayit.mp4

# Testler ve demo üretimi
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python main.py --check
.venv/bin/python main.py --demo --headless --frames 540 --record output/demo-v2.mp4 --preview-dir output/preview-v2
```

Kamera görüntüsü internete gönderilmez ve varsayılan olarak kaydedilmez. İlk kurulumda yaklaşık 8 MB el modeli Google'dan indirilir. Video kaydı sabit 30 FPS zaman tabanı kullanır; kamera daha yavaş çalışırsa kayıttaki hareket hızlanır.

Windows'ta aşağıdaki komutlardaki `.venv/bin/python` yerine `.venv\Scripts\python.exe` kullan. Platform kurulumları yukarıdaki rehberlerdedir.

## Google Meet'te kullanma

1. Bu uygulamayı ve [OBS Studio](https://obsproject.com/) uygulamasını aç.
2. OBS'te **Kaynaklar → Pencere Yakalama** ekle (macOS'ta **macOS Ekran Yakalama → Pencere**); `Limitless | Gojo Hand Techniques` penceresini seç.
3. Görüntüyü tuvale sığdır; gerekirse pencere çerçevesini kırp. **Sanal Kamerayı Başlat / Start Virtual Camera** seç.
4. Google Meet → **Ayarlar → Video → Kamera** bölümünde **OBS Virtual Camera** seç. Listeye gelmezse sanal kamerayı açtıktan sonra Meet sekmesini yenile.

Meet'in arka plan bulanıklığı/efektlerini kapat; yıldızları veya küreleri gizleyebilir. Fiziksel kamerayı Python uygulaması, efektli görüntüyü Meet kullanır. OBS'te ayrıca fiziksel kamera kaynağı eklemek gerekmez.

## Teknik sınırlar ve doğrulama

El noktaları [MediaPipe Hand Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python) ile alınır. Avuç yönü ve başparmak–işaret/orta parmak mesafeleri 3B el noktalarından hesaplanır. Hafif temasta, ekrandaki yakınlık da sınırlı bir derinlik tahmini toleransı sağlar; yalnızca ekranda üst üste gelen, derinlikte uzak parmaklar temas sayılmaz. Avuç yukarı hareketi kameranın yönüne göre tahmin edilir; kamera belirgin biçimde yan yatırılmamalı. Tam yandan veya parmakların birbirini örttüğü açılarda hata olabilir.

Mavinin spiral merkezi, el konumları ile görüntü merkezinden tahmin edilir. Ayrı vücut takibi veya insanın arkasında fiziksel olarak gizlenen 3B küre yoktur; derinlik hissi boyut/parlaklık ve yörüngeyle verilir.

18 Eylül 2026 güncellemesi:

- Yerel Apple M4 ortamında geometri, zamanlama, atış, alan süresi ve göz çizimi otomatik testlerle kontrol edilir. Model kontrolü üç gerçek modeli yükleyip boş görüntüde çıkarım yapar.
- Çaprazlama için bükülü parmak, eklem kesişimi, döndürme/ayna, yan yana parmak reddi, kısa titreme, gerçek takip kaybı ve farklı kare hızları test edilir.
- Göz efekti için iris konumu, göz kırpma, maske sınırı, göz bebeği, alan kapalıyken değişmeme ve kadraj kenarı testleri vardır.
- `docs/github-actions.yml` macOS ve Windows için hazır otomatik test şablonudur. Mevcut GitHub yetkisi workflow yüklemeye izin vermediği için etkinleştirilmedi; otomatik Windows çalıştırması yapılmış değildir. Yetkili bir oturumla `.github/workflows/check.yml` konumuna eklenebilir. Gerçek Windows kamerası ve farklı kullanıcıların çaprazlama başarısı cihaz üzerinde ayrıca denenmelidir; sentetik testler bu ölçümün yerine geçmez.
- Düşük ışık, örtüşen parmaklar, gözlük yansımaları ve çok küçük yüzler takibi zorlaştırabilir. Göz efekti tek yüzü takip eder. İnsan ayırma saç kenarlarında hata yapabilir.

Kod: `gojo/gestures.py` el geometrisi; `gojo/domain.py` alan tetikleme/süre; `gojo/eyes.py` yüz/iris takibi ve mavi gözler; `gojo/engine.py` çağırma/birleşme/atış; `gojo/effects.py` küreler; `gojo/void_effect.py` yıldız ortamı; `gojo/foreground.py` insan ayırma; `scripts/launch.py` ortak kurulum; `scripts/package.py` iki platform paketi.

[Üçüncü taraf bileşenler ve model kaynakları](THIRD_PARTY.md)

[Ayrıntılı doğrulama durumu](docs/VALIDATION.md)
