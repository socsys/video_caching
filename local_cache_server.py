import json
import os
import time

import paramiko
from flask import Flask, request, jsonify
from scp import SCPClient

from lru_cache import LRUCache

app = Flask(__name__)
lru_cache = LRUCache(capacity=3)
download_count = 0
total_response_time_with_cache = 0
total_response_time_without_cache = 0
cache_hits = 0
cache_misses = 0

CHUNK_SIZE = 1024 * 1024  # 1 MB chunks
NODES_FILE = 'nodes.json'
REMOTE_SERVER = 'your_remote_server_ip'
REMOTE_USER = 'your_username'
REMOTE_PASSWORD = 'your_password'
REMOTE_PATH = '/path/to/remote/storage'
LOCAL_CACHE_PATH = '/path/to/local/cache'
METADATA_FILE = 'video_metadata.json'


def load_nodes():
    with open(NODES_FILE, 'r') as f:
        return json.load(f)


NODES = load_nodes()


def create_ssh_client(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def get_video_from_remote_storage(url):
    video_name = os.path.basename(url)
    remote_video_path = os.path.join(REMOTE_PATH, video_name)
    local_video_path = os.path.join(LOCAL_CACHE_PATH, video_name)

    ssh = create_ssh_client(REMOTE_SERVER, 22, REMOTE_USER, REMOTE_PASSWORD)
    scp = SCPClient(ssh.get_transport())

    try:
        scp.get(remote_video_path, local_video_path)
        scp.close()
        return local_video_path
    except FileNotFoundError:
        scp.close()
        return None
    finally:
        ssh.close()


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
    node_ips = list(NODES.values())
    for i, chunk in enumerate(chunks):
        ip = node_ips[i % len(node_ips)]
        if ip not in distribution:
            distribution[ip] = []
        distribution[ip].append(i)
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


def gather_chunks(distribution):
    # This is a placeholder function. In a real implementation, you would
    # actually retrieve the chunks from the specified IP addresses.
    return [f"Chunk {i} from {ip}" for ip, chunks in distribution.items() for i in chunks]


@app.route('/get_video', methods=['GET'])
def get_video():
    global download_count, total_response_time_with_cache, total_response_time_without_cache, cache_hits, cache_misses
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    start_time = time.time()
    cached_distribution = lru_cache.get(url)
    if cached_distribution:
        cache_hits += 1
        chunks = gather_chunks(cached_distribution)
        total_response_time_with_cache += (time.time() - start_time)
        return jsonify({"message": "Video is in cache", "video_chunks": chunks, "from_cache": True}), 200
    else:
        cache_misses += 1
        video_path = get_video_from_remote_storage(url)
        if video_path is None:
            total_response_time_without_cache += (time.time() - start_time)
            return jsonify({"error": "Video not found in remote storage"}), 404

        chunks = chunk_video(video_path)
        distribution = distribute_chunks(chunks)
        save_metadata(url, distribution)

        lru_cache.put(url, distribution)
        download_count += 1
        total_response_time_without_cache += (time.time() - start_time)
        return jsonify(
            {"message": "Video downloaded and cached", "video_chunks": gather_chunks(distribution),
             "from_cache": False}), 200


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
