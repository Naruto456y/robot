import requests
import subprocess
import sys
import os
import time
import json
import threading
from datetime import datetime
import shutil
import re

# 全局变量
CACHE_FILE = "netease_music_cache.json"
MUSIC_CACHE_DIR = "music_cache"
API_URL = "https://music.163.com/api/search/get/web"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://music.163.com/'
}

# 创建缓存目录
if not os.path.exists(MUSIC_CACHE_DIR):
    os.makedirs(MUSIC_CACHE_DIR)

def load_cache():
    """加载缓存数据 Load cached data"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    """保存缓存数据 Save cached data"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def search_music(query, limit=5):
    """
    搜索网易云音乐 Search for NetEase Cloud Music
    """
    cache = load_cache()
    cache_key = f"search_{query}"
    
    # 检查缓存
    if cache_key in cache:
        print("使用缓存数据 Use cached data")
        return cache[cache_key]
    
    params = {
        's': query,
        'type': 1,  # 1: 单曲 single
        'limit': limit,
        'offset': 0
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, data=params)
        response.raise_for_status()
        data = response.json()
        
        if data['code'] == 200 and data['result']['songCount'] > 0:
            songs = []
            for song in data['result']['songs']:
                # 获取艺术家名字 Obtain artist name
                artists = [ar['name'] for ar in song['artists']]
                
                # 获取专辑信息 Get album information
                album = song['album']['name']
                
                # 获取歌曲时长 Obtain the duration of the song
                duration = time.strftime("%M:%S", time.gmtime(song['duration']/1000))
                
                # 获取歌曲ID Get song ID
                song_id = song['id']
                
                songs.append({
                    'id': song_id,
                    'title': song['name'],
                    'artists': artists,
                    'album': album,
                    'duration': duration,
                    'search_query': query  # 保存搜索关键词 Save search keywords
                })
            
            # 保存到缓存 Save to cache
            cache[cache_key] = songs
            save_cache(cache)
            
            return songs
        else:
            print(f"未找到结果(No results found): {data.get('msg', '未知错误(unknown error)')}")
            return []
            
    except Exception as e:
        print(f"搜索出错(Search error): {str(e)}")
        return []

def get_music_url(song_id):
    """
    获取音乐播放URL(Get music playback URL)
    """
    cache = load_cache()
    cache_key = f"url_{song_id}"
    
    # 检查缓存 Check cache
    if cache_key in cache:
        return cache[cache_key]
    
    try: 
        # 使用官方API获取播放链接 Use the official API to obtain playback links
        api_url = f"https://music.163.com/song/media/outer/url?id={song_id}.mp3"
        
        # 保存到缓存
        cache[cache_key] = api_url
        save_cache(cache)
        
        return api_url
    
    except Exception as e:
        print(f"获取音乐URL出错(Error in obtaining music URL): {str(e)}")
    
    return None

def download_music(song_id, url):
    """
    下载音乐到本地缓存 Download music to local cache
    """
    cache_file = os.path.join(MUSIC_CACHE_DIR, f"{song_id}.mp3")
    
    if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
        return cache_file
    
    try:
        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()
        
        with open(cache_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return cache_file
    except Exception as e:
        print(f"下载音乐出错(Error downloading music): {str(e)}")
        return None

def play_with_mplayer(file_path):
    """使用mplayer播放音乐 Play music using Mplayer"""
    try:
        subprocess.run(['mplayer', '-really-quiet', file_path], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL,
                      check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def play_with_vlc(file_path):
    """使用vlc播放音乐 Using VLC to play music"""
    try:
        subprocess.run(['vlc', '--play-and-exit', '--quiet', file_path], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL,
                      check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def play_with_ffplay(file_path):
    """使用ffplay播放音乐 Play music using ffplay"""
    try:
        subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', file_path], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL,
                      check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def play_with_mpv(file_path):
    """使用mpv播放音乐 Using MPV to play music"""
    try:
        subprocess.run(['mpv', '--really-quiet', file_path], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL,
                      check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def play_music(url, song_id):
    """
    播放音乐，自动选择合适的播放器 Play music and automatically select the appropriate player
    """
    if not url:
        print("错误: 没有可用的播放URL")
        print("Error: No available playback URL")
        return False
        
    # 下载音乐到本地缓存
    cache_file = download_music(song_id, url)
    
    if not cache_file or not os.path.exists(cache_file):
        print("错误: 无法下载音乐文件")
        print("Error: Unable to download music files")
        return False
    
    # 尝试使用不同播放器播放
    players = [
        ("mplayer", play_with_mplayer),
        ("vlc", play_with_vlc),
        ("ffplay", play_with_ffplay),
        ("mpv", play_with_mpv)
    ]
    
    player_found = False
    for player_name, player_func in players:
        try:
            if player_func(cache_file):
                player_found = True
                break
        except:
            continue
    
    return player_found

def play_song_directly(query):
    """
    直接播放歌曲: 搜索并播放第一首匹配的歌曲 Play song directly: Search and play the first matching song
    """
    print(f"\n搜索并播放: {query}...")
    results = search_music(query, limit=1)
    
    if not results:
        print("未找到匹配的歌曲(No matching song found)")
        return False
    
    song = results[0]
    artists = ", ".join(song['artists'])
    print(f"找到歌曲(Find a song): {artists} - {song['title']}")
    
    music_url = get_music_url(song['id'])
    if not music_url:
        print("无法获取播放链接,请更换音乐(Unable to obtain playback link, please change music)")
        return False
    
    print("Prepare to play music...")
    


    success = play_music(music_url, song['id'])
    if success:
        print("\n播放完成!(Play completed!)")
    else:
        print("\n播放失败，请检查播放器是否安装 或者 已被重新唤醒打断(Play failed, please check if the player is installed or if it has been awakened and interrupted)")
            
    return True


# def clear_cache():
#     """清除缓存"""
#     try:
#         # 清除搜索缓存
#         if os.path.exists(CACHE_FILE):
#             os.remove(CACHE_FILE)
        
#         # 清除音乐缓存
#         for file in os.listdir(MUSIC_CACHE_DIR):
#             if file.endswith(".mp3"):
#                 os.remove(os.path.join(MUSIC_CACHE_DIR, file))
        
#         print("缓存已清除!")
#     except Exception as e:
#         print(f"清除缓存出错: {str(e)}")

   
def is_mplayer_playing():
    # 检查mplayer进程是否存在 Check if the mplayer process exists
    try:
        # 使用pgrep查找mplayer进程 Using pgrep to search for mplayer processes
        result = subprocess.check_output(['pgrep', '-l', 'mplayer'])
        if not result:
            return False
        return True
    except subprocess.CalledProcessError:
        return False
    

def Car_Music_API(strname='梦然',strmusic='少年'):   
    time.sleep(1.5)
    while is_mplayer_playing():  #等待音频播放完成再播放 Wait for the audio playback to complete before playing again
            pass
           
    user_input = strname + ' '+ strmusic
    print(user_input)
        
    # 默认模式: 直接播放 "歌手 歌名" Default mode: Play the "Singer Song Name" directly
    play_song_directly(user_input)

