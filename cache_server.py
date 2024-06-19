from flask import Flask, request, jsonify
from pytube import YouTube

from lru_cache import LRUCache

app = Flask(__name__)

# Initialize LRU cache with a capacity of 3
lru_cache = LRUCache(capacity=3)


@app.route('/get_video', methods=['GET'])
def get_video():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    cached_video = lru_cache.get(url)
    if cached_video:
        return jsonify({"message": "Video is already in cache", "video_file": cached_video}), 200
    else:
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            video_file = stream.download()
            lru_cache.put(url, video_file)
            return jsonify({"message": "Video downloaded and cached", "video_file": video_file}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
