# Kaynaklar ve üçüncü taraf bileşenler

Efekt çizimleri bu proje için prosedürel olarak üretilir. Repo anime kareleri, sesleri veya video kesitleri içermez. Jujutsu Kaisen / Gojo Satoru adları ve karakterleri hak sahiplerine aittir; bu resmi olmayan bir hayran projesidir.

Python bağımlılıklarının lisansları kendi dağıtımlarındadır; bu dosya onların lisanslarının yerine geçmez:

- [MediaPipe](https://github.com/google-ai-edge/mediapipe): el, yüz/iris ve insan ayırma modelleriyle yerel çıkarım.
- [OpenCV](https://github.com/opencv/opencv): kamera, görüntü işleme ve pencere.
- [NumPy](https://numpy.org/), [Pillow](https://python-pillow.github.io/), [certifi](https://github.com/certifi/python-certifi).
- [PyObjC](https://pyobjc.readthedocs.io/): yalnızca macOS kamera izin akışı.

Modeller repoya veya kaynak ZIP'lerine gömülmez; ilk açılışta Google'ın resmi depolarından indirilir. Model koşulları ve model kartları için:

- [Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
- [Face Landmarker / iris topolojisi](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python)
- [Selfie Segmentation model kartı](https://storage.googleapis.com/mediapipe-assets/Model%20Card%20MediaPipe%20Selfie%20Segmentation.pdf)
- [Face landmark bağlantıları](https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/python/vision/face_landmarker.py)

GitHub Actions macOS/Windows hedefleri [GitHub runner belgelerine](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) göre seçilmiştir.
