import time
from collections import OrderedDict

from flask import Flask, jsonify


class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0

    def get(self, key: str):
        if key not in self.cache:
            self.misses += 1
            return None
        else:
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

    def put(self, key: str, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


app = Flask(__name__)
cache = LRUCache(capacity=100)


@app.route('/video/<video_id>', methods=['GET'])
def get_video(video_id):
    start_time = time.time()
    video = cache.get(video_id)
    if video is None:
        video = f"Video content for {video_id}"
        cache.put(video_id, video)
    response_time = time.time() - start_time
    return jsonify({'video': video, 'response_time': response_time, 'hits': cache.hits, 'misses': cache.misses})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
