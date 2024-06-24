import time

import requests


def request_video(url):
    try:
        start_time = time.time()
        response = requests.get(f'http://0.0.0.0:8000/get_video', params={'url': url})
        total_time = time.time() - start_time
        response.raise_for_status()
        data = response.json()
        if 'video_file' in data:
            print(f"Video file: {data['video_file']}")
        print(f"{data['message']} (Response time: {total_time:.2f} seconds, From cache: {data['from_cache']})")
        return total_time, data['from_cache']
    except requests.RequestException as e:
        print(f"Error requesting video: {e}")
        return None, None


def main():
    urls = [
        # "https://www.youtube.com/watch?v=9bZkp7q19f0",
        # "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        # "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
        "gangnam_style.mp4"
    ]

    total_time_with_cache = 0
    total_time_without_cache = 0
    cache_hits = 0
    cache_misses = 0

    for _ in range(3):
        for url in urls:
            print(f"Requesting video from {url}...")
            total_time, from_cache = request_video(url)
            if total_time is not None:
                if from_cache:
                    total_time_with_cache += total_time
                    cache_hits += 1
                else:
                    total_time_without_cache += total_time
                    cache_misses += 1
            time.sleep(1)

    print("\nMetrics:")
    print(f"Total response time with cache: {total_time_with_cache:.2f} seconds")
    print(f"Total response time without cache: {total_time_without_cache:.2f} seconds")
    print(f"Cache hits: {cache_hits}")
    print(f"Cache misses: {cache_misses}")

    try:
        response = requests.get(f'http://127.0.0.1:8000/metrics')
        response.raise_for_status()
        metrics = response.json()
        print("\nServer Metrics:")
        print(f"Download count: {metrics['download_count']}")
        print(f"Total response time with cache (server): {metrics['total_response_time_with_cache']:.8f} seconds")
        print(f"Total response time without cache (server): {metrics['total_response_time_without_cache']:.8f} seconds")
        print(f"Cache hits (server): {metrics['cache_hits']}")
        print(f"Cache misses (server): {metrics['cache_misses']}")
    except requests.RequestException as e:
        print(f"Error fetching metrics: {e}")


if __name__ == "__main__":
    main()
