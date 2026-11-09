import os

CACHE_FILE = "netease_music_cache.json"
MUSIC_CACHE_DIR = "music_cache"

def clear_cache():
    """清除缓存"""
    try:
        # 清除搜索缓存
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        
        # 清除音乐缓存
        for file in os.listdir(MUSIC_CACHE_DIR):
            if file.endswith(".mp3"):
                os.remove(os.path.join(MUSIC_CACHE_DIR, file))
        
        print("缓存已清除!")
    except Exception as e:
        print(f"清除缓存出错: {str(e)}")
        

clear_cache()
