# import time
#
# import requests
#
#
# def request_video(url):
#     try:
#         start_time = time.time()
#         response = requests.get(f'http://0.0.0.0:8000/get_video', params={'url': url})
#         total_time = time.time() - start_time
#         response.raise_for_status()
#         data = response.json()
#         if 'video_file' in data:
#             print(f"Video file: {data['video_file']}")
#         print(f"{data['message']} (Response time: {total_time:.2f} seconds, From cache: {data['from_cache']})")
#         return total_time, data['from_cache']
#     except requests.RequestException as e:
#         print(f"Error requesting video: {e}")
#         return None, None
#
#
# def main():
#     urls = [
#         # "https://www.youtube.com/watch?v=9bZkp7q19f0",
#         # "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
#         # "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
#         "gangnam_style.mp4"
#     ]
#
#     total_time_with_cache = 0
#     total_time_without_cache = 0
#     cache_hits = 0
#     cache_misses = 0
#
#     for _ in range(3):
#         for url in urls:
#             print(f"Requesting video from {url}...")
#             total_time, from_cache = request_video(url)
#             if total_time is not None:
#                 if from_cache:
#                     total_time_with_cache += total_time
#                     cache_hits += 1
#                 else:
#                     total_time_without_cache += total_time
#                     cache_misses += 1
#             time.sleep(1)
#
#     print("\nMetrics:")
#     print(f"Total response time with cache: {total_time_with_cache:.2f} seconds")
#     print(f"Total response time without cache: {total_time_without_cache:.2f} seconds")
#     print(f"Cache hits: {cache_hits}")
#     print(f"Cache misses: {cache_misses}")
#
#     try:
#         response = requests.get(f'http://127.0.0.1:8000/metrics')
#         response.raise_for_status()
#         metrics = response.json()
#         print("\nServer Metrics:")
#         print(f"Download count: {metrics['download_count']}")
#         print(f"Total response time with cache (server): {metrics['total_response_time_with_cache']:.8f} seconds")
#         print(f"Total response time without cache (server): {metrics['total_response_time_without_cache']:.8f} seconds")
#         print(f"Cache hits (server): {metrics['cache_hits']}")
#         print(f"Cache misses (server): {metrics['cache_misses']}")
#     except requests.RequestException as e:
#         print(f"Error fetching metrics: {e}")
#
#
# if __name__ == "__main__":
#     main()


# import requests
# import time
# import random


# def client():
#     with open('video_ids.txt', 'r') as f:
#         video_ids = f.read().splitlines()
#
#     # Simulate 1000 random requests from the 100 video IDs
#     request_ids = [random.choice(video_ids) for _ in range(10000)]
#
#     response_times = []
#     total_hits = 0
#     total_misses = 0
#
#     for video_id in request_ids:
#         start_time = time.time()
#         response = requests.get(f'http://localhost:8000/video/{video_id}')
#         response_time = time.time() - start_time
#         response_data = response.json()
#         response_times.append(response_data['response_time'])
#         total_hits = response_data['hits']
#         total_misses = response_data['misses']
#         print(f"Requested {video_id}, response time: {response_time:.6f}s, "
#               f"cache hits: {total_hits}, cache misses: {total_misses}")
#
#     print(f"Average response time: {sum(response_times) / len(response_times):.6f}s")
#     print(f"Total cache hits: {total_hits}")
#     print(f"Total cache misses: {total_misses}")
#
#
# client()

# video_client.py
import time

import requests

SERVER_URL = "http://127.0.0.1:9000"
VIDEO_URL = "http://example.com/path/to/your/200MB_1080p_video.mp4"


def request_chunk(video_url, chunk_index):
    try:
        response = requests.get(f"{SERVER_URL}/get_chunk", params={"url": video_url, "index": chunk_index})
        response.raise_for_status()
        data = response.json()
        return data['chunk']
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None


def simulate_watching(video_url, total_chunks):
    for i in range(total_chunks):
        print(f"Requesting chunk {i + 1}/{total_chunks}")
        chunk = request_chunk(video_url, i)
        if chunk is None:
            print(f"Error retrieving chunk {i}")
            break
        print(f"Watching chunk {i + 1}/{total_chunks}")
        time.sleep(1)  # Simulate watching time


def main():
    # Assume we know the total number of chunks beforehand
    total_chunks = 20  # For example, 20 chunks for the video
    simulate_watching(VIDEO_URL, total_chunks)


if __name__ == "__main__":
    main()
