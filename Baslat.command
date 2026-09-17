#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if [[ -x .venv/bin/python ]]; then
  .venv/bin/python scripts/launch.py "$@"
elif command -v python3 >/dev/null 2>&1; then
  python3 scripts/launch.py "$@"
else
  printf 'Python bulunamadi. python.org adresinden Python 3.12 kurun.\n'
  read -r '?Kapatmak için Enter…'
  exit 1
fi
result=$?
if (( result != 0 )); then
  printf '\nBaşlatılamadı. Yukarıdaki hata mesajını kontrol edin.\n'
  read -r '?Kapatmak için Enter…'
fi
exit $result
