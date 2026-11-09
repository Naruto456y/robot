import yt_dlp

def download_audio_from_youtube(video_url, output_filename='audio'):
    """
    Скачивает аудио с видео на YouTube и сохраняет в MP3.

    Args:
        video_url (str): Ссылка на видео YouTube.
        output_filename (str): Желаемое имя выходного файла (без расширения).
    """
    ydl_opts = {
        'format': 'bestaudio/best',  # Выбирает лучший доступный аудиопоток
        'postprocessors': [{  # Конвертирует в MP3
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # Качество MP3 (битрейт)
        }],
        'outtmpl': f'{output_filename}.%(ext)s',  # Шаблон имени файла
        'quiet': False,  # Показывать прогресс загрузки в консоли
        'no_warnings': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Начинаю загрузку и конвертацию аудио из: {video_url}")
            ydl.download([video_url])
        print(f"\nГотово! Аудио сохранено как '{output_filename}.mp3'")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    # Используем извлеченную ссылку
    youtube_url = "http://www.youtube.com/watch?v=ZLwTSpyL_oE"
    # Задайте желаемое имя для mp3 файла
    output_name = "kobyakov_laugh"

    download_audio_from_youtube(youtube_url, output_name)