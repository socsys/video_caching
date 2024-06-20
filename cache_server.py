import os
import time

from flask import Flask, request, jsonify
from pytube import YouTube

from lru_cache import LRUCache

app = Flask(__name__)

lru_cache = LRUCache(capacity=3)

download_count = 0
total_response_time_with_cache = 0
total_response_time_without_cache = 0
cache_hits = 0
cache_misses = 0


@app.route('/get_video', methods=['GET'])
def get_video():
    global download_count, total_response_time_with_cache, total_response_time_without_cache, cache_hits, cache_misses

    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    start_time = time.time()
    cached_video = lru_cache.get(url)
    if cached_video and os.path.exists(cached_video):
        cache_hits += 1
        total_response_time_with_cache += (time.time() - start_time)
        return jsonify({"message": "Video is already in cache", "video_file": cached_video, "from_cache": True}), 200
    else:
        cache_misses += 1
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            video_file = stream.download()
            lru_cache.put(url, video_file)
            download_count += 1
            total_response_time_without_cache += (time.time() - start_time)
            return jsonify(
                {"message": "Video downloaded and cached", "video_file": video_file, "from_cache": False}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify({
        "download_count": download_count,
        "total_response_time_with_cache": total_response_time_with_cache,
        "total_response_time_without_cache": total_response_time_without_cache,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
