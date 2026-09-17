#!/usr/bin/env python3
"""Gojo-inspired camera effects. Run python main.py --help for controls."""
import argparse
from pathlib import Path
import sys
import time
import cv2
import numpy as np
from gojo.engine import Technique
from gojo.effects import Renderer
from gojo.demo import demo_frame, domain_demo_frame
from gojo.tracker import MODEL, Tracker, download_model
from gojo.camera import ensure_camera_permission
from gojo.foreground import Foreground
from gojo.eyes import EyeTracker, blue_eyes

TITLE = 'Limitless | Gojo Hand Techniques'


def arguments():
    parser = argparse.ArgumentParser(description='Kamerada Gojo: sol mavi, sağ kırmızı, birleşince mor.')
    parser.add_argument('--camera', type=int, default=0, help='Kamera numarası (varsayılan: 0)')
    parser.add_argument('--width', type=int, default=1280, help='Görüntü genişliği; yavaşsa 960')
    parser.add_argument('--height', type=int, default=720)
    parser.add_argument('--swap-hands', action='store_true', help='Sağ/sol algısını ters çevir')
    parser.add_argument('--reduced-effects', action='store_true', help='Daha az parçacık ve parlama')
    parser.add_argument('--demo', action='store_true', help='Kamerasız sentetik koreografi')
    parser.add_argument('--demo-domain', action='store_true', help='Kamerasız Sonsuz Boşluk demosu (16 sn)')
    parser.add_argument('--headless', action='store_true', help='Pencere açmadan sınırlı test')
    parser.add_argument('--frames', type=int, default=0, help='Bu kadar kare sonra çık (0: sınırsız)')
    parser.add_argument('--record', type=Path, help='Efektli görüntüyü belirtilen MP4 dosyasına kaydet')
    parser.add_argument('--preview-dir', type=Path, help='Yalnızca demodan örnek PNG kareleri kaydet')
    parser.add_argument('--download-model', action='store_true', help='Üç takip modelini indir ve çık')
    parser.add_argument('--check', action='store_true', help='Üç modeli yükle ve boş karede çıkarım doğrula')
    parser.add_argument('--no-eye-glow', action='store_true', help='Göz takibini kapat (düşük donanım)')
    args = parser.parse_args()
    if args.demo_domain:
        args.demo = True
    if args.frames < 0 or not (640 <= args.width <= 2560 and 360 <= args.height <= 1440):
        parser.error('frames >= 0, genişlik 640–2560, yükseklik 360–1440 olmalı.')
    if args.headless and not args.frames:
        args.frames = 480 if args.demo_domain else (540 if args.demo else 30)
    if args.preview_dir and not args.demo:
        parser.error('--preview-dir yalnızca --demo ile kullanılır.')
    return args


def main():
    args = arguments()
    tracker = capture = writer = foreground = eye_tracker = None
    window_created = False
    try:
        if args.download_model:
            print(download_model())
            from gojo.foreground import MODEL as SEGMENT_MODEL, URL as SEGMENT_URL
            from gojo.eyes import MODEL as FACE_MODEL, URL as FACE_URL
            print(download_model(SEGMENT_MODEL, SEGMENT_URL, 100_000, 'Arka plan modeli'))
            print(download_model(FACE_MODEL, FACE_URL, 1_000_000, 'Göz takip modeli'))
            return 0
        if args.check:
            tracker = Tracker(download_model(), args.swap_hands)
            hands = tracker.detect(np.zeros((480,640,3),np.uint8), 0.)
            foreground, eye_tracker = Foreground(), EyeTracker()
            blank = np.zeros((480,640,3),np.uint8)
            mask, eyes = foreground.mask(blank,0.), eye_tracker.detect(blank,0.)
            print(f'Üç model çıkarımı başarılı. Boş kare: {len(hands)} el, {len(eyes)} göz. Maske: {mask.shape}. OpenCV {cv2.__version__}')
            return 0
        if not args.demo:
            ensure_camera_permission()
            tracker = Tracker(download_model(), args.swap_hands)
            try:
                foreground = Foreground()
            except (RuntimeError,OSError,ValueError) as exc:
                print(f'Arka plan ayırma yüklenemedi; alan efekti saydam kamera katmanıyla çalışacak: {exc}',file=sys.stderr)
            if not args.no_eye_glow:
                try:
                    eye_tracker = EyeTracker()
                except (RuntimeError,OSError,ValueError) as exc:
                    print(f'Göz takibi yüklenemedi; mavi göz efekti kapalı: {exc}',file=sys.stderr)
            capture = cv2.VideoCapture(args.camera, cv2.CAP_AVFOUNDATION if sys.platform == 'darwin' else cv2.CAP_ANY)
            if not capture.isOpened():
                permission = ('macOS Sistem Ayarları > Gizlilik ve Güvenlik > Kamera bölümünden Terminal’e izin verin'
                              if sys.platform == 'darwin' else 'Windows Ayarlar > Gizlilik ve güvenlik > Kamera bölümünden masaüstü uygulamalarına izin verin')
                raise RuntimeError(f'Kamera açılamadı. {permission}; başka kamera için --camera 1 deneyin.')
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
            capture.set(cv2.CAP_PROP_FPS, 30)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        state, renderer = Technique(), Renderer(args.reduced_effects)
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
        if not args.headless:
            cv2.namedWindow(TITLE, cv2.WINDOW_NORMAL)
            window_created = True
            cv2.resizeWindow(TITLE, args.width, args.height)
        print('R sıfırla · D takip noktaları · S sağ/sol · L hafif efekt · Q çık', flush=True)
        print('Kırmızı: sağ elde iki parmak. Mavi: sol avuç yukarı açık. Atış: başparmak + işaret veya orta parmak '
              'önce ayrık, sonra uçları 0,3 sn hafif temas; beyaz halka oluşunca hızlıca ayır.', flush=True)
        print('Alan genişletme: işaret ve orta parmağı çaprazla, diğer iki parmağı kapat; yaklaşık 0,55 sn tut. Süre: 12 sn.',flush=True)
        if args.demo:
            print('Sentetik demo: el hareketleri simüle edilir; kamera takibi testi değildir.', flush=True)
        start = previous = time.monotonic()
        count, fps, missing, detected_frames = 0, 30., 0, 0
        phases, shots = set(), set()
        while not args.frames or count < args.frames:
            wall = time.monotonic()
            now = count / 30 if args.demo else wall - start
            if args.demo:
                make_frame = domain_demo_frame if args.demo_domain else demo_frame
                frame, hands = make_frame(now, args.width, args.height)
            else:
                ok, frame = capture.read()
                if not ok:
                    missing += 1
                    if missing >= 15:
                        raise RuntimeError('Kameradan görüntü alınamıyor. Kamerayı kullanan diğer uygulamaları kapatıp tekrar deneyin.')
                    time.sleep(.03)
                    continue
                missing = 0
                frame = cv2.flip(frame, 1)
                if frame.shape[1] != args.width:
                    frame = cv2.resize(frame, (args.width, round(frame.shape[0] * args.width / frame.shape[1])))
                hands = tracker.detect(frame, now)
                detected_frames += bool(hands)
            state.viewport = (frame.shape[1], frame.shape[0])
            state.update(hands, now)
            person_mask, eyes = None, []
            if state.domain.active(now):
                phases.add('domain')
                if args.demo:
                    person_mask = np.zeros(frame.shape[:2],np.float32)
                elif foreground:
                    try:
                        person_mask = foreground.mask(frame,now)
                    except (RuntimeError,ValueError,cv2.error) as exc:
                        print(f'Arka plan ayırma durdu; saydam katmana geçiliyor: {exc}',file=sys.stderr)
                        foreground.close()
                        foreground = None
                if eye_tracker:
                    try:
                        eyes = eye_tracker.detect(frame,now)
                    except (RuntimeError,ValueError,cv2.error) as exc:
                        print(f'Göz takibi durdu; mavi göz efekti kapalı: {exc}',file=sys.stderr)
                        eye_tracker.close()
                        eye_tracker = None
            phases.add(state.phase)
            shots.update(p.kind for p in state.projectiles)
            fps = fps*.92 + .08 / max(wall-previous, .001)
            previous = wall
            output = renderer.render(frame, state, now, fps, args.demo, tracker.swap if tracker else False,person_mask)
            output = blue_eyes(output,eyes,state.domain.strength(now),now)
            if args.record:
                if writer is None:
                    args.record.parent.mkdir(parents=True, exist_ok=True)
                    writer = cv2.VideoWriter(str(args.record), cv2.VideoWriter_fourcc(*'mp4v'), 30,
                                             (output.shape[1], output.shape[0]))
                    if not writer.isOpened():
                        raise RuntimeError(f'Video yazıcısı açılamadı: {args.record}')
                writer.write(output)
            captures = (15,65,120,260,410,455) if args.demo_domain else (45,73,160,220,402,462,480)
            if args.preview_dir and count in captures:
                stage = 'domain' if state.domain.active(now) else state.phase
                cv2.imwrite(str(args.preview_dir / f'{count:03d}-{stage}.png'), output)
            count += 1
            if not args.headless:
                cv2.imshow(TITLE, output)
                delay = max(1, round((count/30 - (time.monotonic()-start))*1000)) if args.demo else 1
                key = cv2.waitKey(min(delay, 34)) & 0xFF
                if key in (27, ord('q')):
                    break
                if key == ord('r'):
                    state.reset()
                    renderer.particles.clear()
                elif key == ord('d'):
                    renderer.debug = not renderer.debug
                elif key == ord('l'):
                    renderer.reduced = not renderer.reduced
                elif key == ord('s') and tracker:
                    tracker.swap = not tracker.swap
                    state.reset()
                if cv2.getWindowProperty(TITLE, cv2.WND_PROP_VISIBLE) < 1:
                    break
        elapsed = time.monotonic()-start
        print(f'Tamamlandı: {count} kare, {elapsed:.2f} saniye, işlem ortalaması {count/max(elapsed,.001):.1f} FPS.')
        print(f'Aşamalar: {", ".join(sorted(phases))}. El bulunan gerçek kamera karesi: {detected_frames}.')
        print(f'Fırlatılan renkler: {", ".join(sorted(shots)) or "yok"}.')
        return 0
    except (RuntimeError, OSError, ValueError, cv2.error) as exc:
        print(f'Hata: {exc}', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        if writer:
            writer.release()
        if capture:
            capture.release()
        if tracker:
            tracker.close()
        if foreground:
            foreground.close()
        if eye_tracker:
            eye_tracker.close()
        if window_created:
            cv2.destroyAllWindows()


if __name__ == '__main__':
    raise SystemExit(main())
