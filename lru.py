from collections import OrderedDict

from pytube import YouTube


class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str):
        if key not in self.cache:
            return None
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


def download_video(url: str):
    yt = YouTube(url)
    print("title is:", yt.title)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
    video_file = stream.download()
    return video_file


def main():
    lru_cache = LRUCache(capacity=3)

    # List of YouTube URLs to cache
    urls = [
        "http://www.youtube.com/watch?v=eb1Hg0T8gCU",
        "http://www.youtube.com/watch?v=8_eAKb4HLe4",
        "http://www.youtube.com/watch?v=JHJN1t3uIng",
        "http://www.youtube.com/watch?v=vPCexNhxP8o"
    ]

    for url in urls:
        cached_video = lru_cache.get(url)
        if cached_video:
            print(f"Video from {url} is already in cache.")
        else:
            print(f"Downloading video from {url}...")
            video_file = download_video(url)
            lru_cache.put(url, video_file)
            print(f"Video from {url} downloaded and cached.")

    print("\nCache content:")
    for url, video in lru_cache.cache.items():
        print(f"URL: {url}, Video file: {video}")


if __name__ == "__main__":
    main()
