# macOS kurulumu

Hedef: Apple Silicon (M1/M2/M3/M4 veya üstü), macOS 13+, Python 3.12–3.14. Önerilen Python sürümü 3.12. Sabitlenen MediaPipe sürümünde Intel Mac wheel dosyası olmadığından Intel Mac bu paketin desteklenen hedefi değildir.

1. [python.org](https://www.python.org/downloads/macos/) üzerinden Python'u kur.
2. GitHub'da **Code → Download ZIP** ile projeyi indir ve ZIP'i çıkar.
3. **Baslat.command** dosyasını çalıştır. İlk açılışta bağımlılıklar ve modeller indirilir.
4. macOS kamera izni sorarsa izin ver. Daha önce reddettiysen **Sistem Ayarları → Gizlilik ve Güvenlik → Kamera** bölümünden kullandığın Terminal uygulamasına izin ver.

Dosyanın çalıştırma izni yoksa proje klasöründe Terminal aç:

```sh
chmod +x Baslat.command
./Baslat.command
```

Manuel kurulum:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

`Baslat.command --camera 1` ile başka kamera, `--width 960 --height 540 --reduced-effects` ile daha hafif görüntü seçebilirsin. `--no-eye-glow` yüz modelini devre dışı bırakır.
