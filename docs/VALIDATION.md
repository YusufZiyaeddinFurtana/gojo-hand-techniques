# Doğrulama durumu

18 Eylül 2026, yerel Apple M4 / Python 3.14 / OpenCV 4.14 / MediaPipe 0.10.35:

- **86 otomatik test başarılı.** El geometrisi, atış sırası, alan zamanlaması, iris çizimi, kapalı göz ve kadraj dışı koordinatlar dahil.
- `main.py --check`: el, insan ayırma ve yüz/iris modelleri yüklendi; boş kare çıkarımları başarılı.
- 540 karelik sentetik enerji demosu: kırmızı, mavi ve mor atışları ile birleşme tamamlandı.
- 480 karelik sentetik alan demosu: tetikleme, 12 saniyelik etki ve normale dönüş tamamlandı.
- Canlı kamera + insan ayırma + yüz modeli + alan çizimi 12 kare boyunca birlikte çalıştı; görüntüler kaydedilmedi. Bu denemede göz saptanmadığı için gerçek yüzde mavi göz görünümünü doğruladığı iddia edilmez. İris çizimi sentetik göz verisiyle kontrol edildi.
- Gerçek kullanıcının çapraz parmak başarı oranı ve Windows fiziksel kamerası ayrıca denenmelidir.

GitHub Actions sonuçları repo **Actions** sekmesindedir. İş akışı Windows x64 ve macOS ARM64 üzerinde kurulum, 86 test, üç modelin çıkarımı, sentetik demolar ve ZIP paketlemeyi çalıştırır. Bu dosyadaki yerel sonuçlar bir Windows donanım testi anlamına gelmez.
