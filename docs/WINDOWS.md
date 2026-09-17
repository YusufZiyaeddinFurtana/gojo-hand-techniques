# Windows kurulumu

Hedef: Windows 10/11, x64 işlemci ve 64-bit Python 3.12. Bu sürüm Python kaynak kodu + çift tıklanabilir başlatıcıdır; bağımsız bir `.exe` değildir.

1. [python.org](https://www.python.org/downloads/windows/) üzerinden Python 3.12'nin **Windows installer (64-bit)** sürümünü kur. Kurulumda **Add python.exe to PATH** seçeneğini aç.
2. GitHub'da **Code → Download ZIP** ile projeyi indir ve ZIP'i bir klasöre çıkar. ZIP içinden çalıştırma.
3. **Baslat.bat** dosyasına çift tıkla. İlk çalıştırma `.venv` oluşturur, paketleri ve üç modeli indirir; internet gerekir. Sonraki açılışlarda modeller yerelden yüklenir.
4. Kamera izni gerekiyorsa **Ayarlar → Gizlilik ve güvenlik → Kamera → Masaüstü uygulamalarının kameranıza erişmesine izin ver** seçeneğini aç.

Terminalden seçenekler:

```bat
Baslat.bat --camera 1
Baslat.bat --width 960 --height 540 --reduced-effects
Baslat.bat --no-eye-glow
Baslat.bat --demo-domain
```

Manuel kurulum (CMD veya PowerShell):

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

**Kamera bulunamıyorsa:** Teams, Discord, OBS gibi kamerayı kullanan uygulamaları kapat; `--camera 1` dene. Meet'te efektli görüntü için README'deki OBS yöntemini kullan.

**Paket kurulamadıysa:** 32-bit Python veya Windows ARM64 yerine x64 Python kullandığını kontrol et. Bu paket sürümleri için Windows x64 wheel dosyaları vardır; yerelde Windows cihazı üzerinde kamera testi yapılmamıştır. Windows x64 / Python 3.12 bağımlılıkları için wheel uyumluluğu kontrol edilir; bu kontrol gerçek Windows çalıştırmasının yerine geçmez. Otomatik test şablonu `docs/github-actions.yml` içindedir, henüz etkin değildir.
