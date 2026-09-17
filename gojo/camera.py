"""Request macOS camera access before OpenCV tries to open a capture session."""
import sys
import threading
import time


class CameraPermissionError(RuntimeError):
    pass


def _authorize_camera(device, media_type, pump, timeout=60):
    # AVAuthorizationStatus: notDetermined=0, restricted=1, denied=2, authorized=3.
    status = int(device.authorizationStatusForMediaType_(media_type))
    if status == 3:
        return
    if status in (1, 2):
        raise CameraPermissionError(
            'macOS kamera erişimini engelliyor. Sistem Ayarları > Gizlilik ve Güvenlik > '
            'Kamera bölümünde bu dosyayı açan Terminal uygulamasının iznini etkinleştir '
            '(Terminal, iTerm veya kullandığın terminal). Ardından Baslat.command dosyasını yeniden aç.')
    completed = threading.Event()
    result = []

    def answer(granted):
        result.append(bool(granted))
        completed.set()

    print('Kamera izni bekleniyor… macOS penceresinde “İzin Ver” seç. '
          'Pencere görünmüyorsa diğer pencerelerin arkasını kontrol et.', flush=True)
    device.requestAccessForMediaType_completionHandler_(media_type, answer)
    deadline = time.monotonic() + timeout
    while not completed.is_set() and time.monotonic() < deadline:
        pump()
    if not completed.is_set():
        raise CameraPermissionError(
            'Kamera izin isteği 60 saniyede yanıtlanmadı. Sistem Ayarları > Gizlilik ve Güvenlik > '
            'Kamera bölümünü kontrol et. İzni verdikten sonra Baslat.command dosyasını yeniden aç.')
    if not result[0]:
        raise CameraPermissionError(
            'Kamera izni verilmedi. Sistem Ayarları > Gizlilik ve Güvenlik > Kamera bölümünde '
            'kullandığın Terminal uygulamasına izin verip yeniden başlat.')
    print('Kamera izni alındı; kamera açılıyor…', flush=True)


def ensure_camera_permission():
    if sys.platform != 'darwin':
        return
    try:
        from AVFoundation import AVCaptureDevice, AVMediaTypeVideo
        from Foundation import NSDate, NSRunLoop, NSDefaultRunLoopMode
    except ImportError as exc:
        raise RuntimeError('Kamera izin bileşeni eksik. Baslat.command ile başlat veya '
                           '.venv/bin/python -m pip install -r requirements.txt çalıştır.') from exc

    def pump():
        NSRunLoop.currentRunLoop().runMode_beforeDate_(
            NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(.1))

    _authorize_camera(AVCaptureDevice, AVMediaTypeVideo, pump)
