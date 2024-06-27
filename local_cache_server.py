import json
import os
import time
import random

from flask import Flask, request, jsonify
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

from lru_cache import LRUCache

app = Flask(__name__)
lru_cache = LRUCache(capacity=3)
download_count = 0
total_response_time_with_cache = 0
total_response_time_without_cache = 0
cache_hits = 0
cache_misses = 0

CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB chunks
NODES_FILE = 'nodes.json'
GROUND_STATION_IP = "127.0.0.1"
GROUND_STATION_USER = "root"
GROUND_STATION_PASSWORD = ""
REMOTE_PATH = '/path/to/remote/storage'
LOCAL_CACHE_PATH = '/path/to/local/cache'
METADATA_FILE = 'video_metadata.json'


def load_nodes():
    with open(NODES_FILE, 'r') as f:
        return json.load(f)


NODES = load_nodes()


def create_ssh_client(server, port, user, password):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


# def get_video_chunks_from_remote_storage(url):
#     video_name = os.path.basename(url)
#     remote_video_path = os.path.join(REMOTE_PATH, video_name)
#     local_chunks_path = os.path.join(LOCAL_CACHE_PATH, video_name + "_chunks")
#
#     if not os.path.exists(local_chunks_path):
#         os.makedirs(local_chunks_path)
#
#     ssh = create_ssh_client(GROUND_STATION_IP, 22, GROUND_STATION_USER, GROUND_STATION_PASSWORD)
#     scp = SCPClient(ssh.get_transport())
#
#     try:
#         # Request chunking and retrieve chunks
#         stdin, stdout, stderr = ssh.exec_command(
#             f"python3 /Users/sf0059/Dev/caching_implementation/video_caching/remote_video_storage.py "
#             f"./cache_storage/gangnam_style.mp4")
#         if stderr.read():
#             print("Error in remote chunking:", stderr.read().decode())
#             return None
#
#         chunk_files = stdout.read().decode().split()
#
#         for chunk_file in chunk_files:
#             scp.get(chunk_file, os.path.join(local_chunks_path, os.path.basename(chunk_file)))
#
#         scp.close()
#         return local_chunks_path
#     except Exception as e:
#         print(f"Error retrieving video chunks: {str(e)}")
#         return None
#     finally:
#         ssh.close()


def get_video_chunks_from_remote_storage(url):
    video_name = os.path.basename(url)
    remote_video_path = os.path.join(REMOTE_PATH, video_name)
    local_chunks_path = os.path.join(LOCAL_CACHE_PATH, video_name + "_chunks")

    if not os.path.exists(local_chunks_path):
        os.makedirs(local_chunks_path)

    ssh = create_ssh_client(GROUND_STATION_IP, 22, GROUND_STATION_USER, GROUND_STATION_PASSWORD)

    try:
        # Simulate remote chunking
        print(f"Simulating remote chunking for {video_name}")
        time.sleep(2)  # Simulate processing time on the remote server

        # Simulate SCP transfer
        num_chunks = random.randint(15, 25)  # Simulate a 150-250 MB video in 10 MB chunks

        for i in range(num_chunks):
            chunk_size = random.randint(9 * 1024 * 1024, 10 * 1024 * 1024)  # 9-10 MB chunks
            chunk_data = os.urandom(chunk_size)  # Generate random data for the chunk
            chunk_file_path = os.path.join(local_chunks_path, f"chunk_{i:03d}")

            with open(chunk_file_path, 'wb') as f:
                f.write(chunk_data)

            # Simulate SCP transfer time
            time.sleep(0.5)  # Adjust this value to simulate different network speeds
            print(f"Transferred chunk_{i:03d} from remote storage")

        print(f"Completed transfer of {num_chunks} chunks for {video_name}")
        return local_chunks_path
    except Exception as e:
        print(f"Error retrieving video chunks: {str(e)}")
        return None
    finally:
        ssh.close()


def save_metadata(url, chunks_path):
    metadata = {}
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
    metadata[url] = chunks_path
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
    cached_chunks_path = lru_cache.get(url)
    if cached_chunks_path:
        cache_hits += 1
        chunks = [open(os.path.join(cached_chunks_path, f)).read() for f in sorted(os.listdir(cached_chunks_path))]
        total_response_time_with_cache += (time.time() - start_time)
        return jsonify({"message": "Video is in cache", "video_chunks": chunks, "from_cache": True}), 200
    else:
        cache_misses += 1
        chunks_path = get_video_chunks_from_remote_storage(url)

        if chunks_path is None:
            total_response_time_without_cache += (time.time() - start_time)
            return jsonify({"error": "Video not found in remote storage"}), 404

        save_metadata(url, chunks_path)
        lru_cache.put(url, chunks_path)
        download_count += 1

        chunks = [open(os.path.join(chunks_path, f), 'rb').read() for f in sorted(os.listdir(chunks_path))]
        total_response_time_without_cache += (time.time() - start_time)
        return jsonify({"message": "Video downloaded and cached", "video_chunks": chunks, "from_cache": False}), 200


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
    app.run(host='0.0.0.0', port=9000)
