import json
import os
import random
import time

from flask import Flask, request, jsonify

from lru_cache import LRUCache

app = Flask(__name__)
lru_cache = LRUCache(capacity=3)
download_count = 0
total_response_time_with_cache = 0
total_response_time_without_cache = 0
cache_hits = 0
cache_misses = 0

CHUNK_SIZE = 1024 * 1024  # 1 MB chunks
NODES = ['star1', 'star2', 'star3']
LOCAL_STORAGE = './video_caching/cache_storage/'  # Replace with actual path
METADATA_FILE = './video_caching/chunks_storage/metadata.json'


def simulate_network_delay():
    # Simulate network delay between 50ms to 500ms
    time.sleep(random.uniform(0.05, 0.5))


def get_video_from_local_storage(url):
    # Simulate fetching video from local storage
    simulate_network_delay()
    video_path = os.path.join(LOCAL_STORAGE, os.path.basename(url))
    print(video_path)
    if os.path.exists(video_path):
        return video_path
    else:
        raise FileNotFoundError(f"Video not found in local storage: {url}")


def chunk_video(video_path):
    chunks = []
    with open(video_path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks


def distribute_chunks(chunks):
    distribution = {}
    for i, chunk in enumerate(chunks):
        node = NODES[i % len(NODES)]
        if node not in distribution:
            distribution[node] = []
        distribution[node].append(i)
    return distribution


def save_metadata(url, distribution):
    metadata = {}
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    metadata[url] = distribution
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)


def get_metadata(url):
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        return metadata.get(url)
    return None


@app.route('/get_video', methods=['GET'])
def get_video():
    global download_count, total_response_time_with_cache, total_response_time_without_cache, cache_hits, cache_misses
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    start_time = time.time()
    cached_video = lru_cache.get(url)
    if cached_video:
        cache_hits += 1
        total_response_time_with_cache += (time.time() - start_time)
        return jsonify({"message": "Video is already in cache", "video_chunks": cached_video, "from_cache": True}), 200
    else:
        cache_misses += 1
        try:
            video_path = get_video_from_local_storage(url)
            chunks = chunk_video(video_path)
            distribution = distribute_chunks(chunks)
            save_metadata(url, distribution)

            lru_cache.put(url, distribution)
            download_count += 1
            total_response_time_without_cache += (time.time() - start_time)
            return jsonify(
                {"message": "Video downloaded and cached", "video_chunks": distribution, "from_cache": False}), 200
        except Exception as e:
            print(e)
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
