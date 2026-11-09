#!/bin/bash
# Запуск OLED-анимаций:  ./play.sh            — меню
#                        ./play.sh naruto     — сразу запустить (имя или номер)
#                        ./play.sh coding 0.05 — доп. аргумент (громкость у мультиков со звуком)
# Остановка анимации: Ctrl+C. Стандартный экран возвращается сам.
DIR="$(cd "$(dirname "$0")" && pwd)"
NAMES=(claude naruto chidori cartoon coding)
FILES=(oled_claude_anim.py oled_naruto.py oled_chidori.py oled_cartoon.py oled_coding.py)
TITLES=("Claude Code — человечек ходит и печатает" "Наруто — лицо, расенган, сюрикен, Коноха" "Чидори — три печати и молния" "Маленький робот и звезда (тихий звук)" "Пишем код — ошибка, исправление, успех (тихий звук)")

run() { exec python3 "$DIR/${FILES[$1]}" "${@:2}"; }

pick="$1"
if [ -z "$pick" ]; then
  echo "OLED-анимации:"
  for i in "${!NAMES[@]}"; do printf "  %d) %-8s %s\n" $((i+1)) "${NAMES[$i]}" "${TITLES[$i]}"; done
  read -rp "Номер или имя: " pick
fi
for i in "${!NAMES[@]}"; do
  if [ "$pick" = "${NAMES[$i]}" ] || [ "$pick" = "$((i+1))" ]; then run "$i" "${@:2}"; fi
done
echo "Не нашёл анимацию «$pick»" >&2; exit 1
