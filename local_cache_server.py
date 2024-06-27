import json
import logging
import os
import time
from datetime import datetime

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
total_data_sent_to_satellites = 0
total_data_sent_to_clients = 0

CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB chunks
NODES_FILE = 'nodes.json'
HANDOFF_FILE = 'handoff.json'
GROUND_STATION_IP = "127.0.0.1"
GROUND_STATION_USER = os.getenv("GROUND_STATION_USER")
GROUND_STATION_PASSWORD = os.getenv("GROUND_STATION_PASSWORD")
REMOTE_PATH = '/path/to/remote/storage'
LOCAL_CACHE_PATH = '/path/to/local/cache'
METADATA_FILE = 'video_metadata.json'

logging.basicConfig(level=logging.INFO)


def load_nodes():
    with open(NODES_FILE, 'r') as f:
        return json.load(f)


def load_handoff():
    with open(HANDOFF_FILE, 'r') as f:
        return json.load(f)


NODES = load_nodes()
HANDOFF = load_handoff()


def create_ssh_client(server, port, user, password):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def get_video_chunks_from_remote_storage(url):
    video_name = os.path.basename(url)
    remote_video_path = os.path.join(REMOTE_PATH, video_name)
    local_chunks_path = os.path.join(LOCAL_CACHE_PATH, video_name + "_chunks")

    if not os.path.exists(local_chunks_path):
        os.makedirs(local_chunks_path)

    ssh = create_ssh_client(GROUND_STATION_IP, 22, GROUND_STATION_USER, GROUND_STATION_PASSWORD)

    try:
        logging.info(f"Simulating remote chunking for {video_name}")
        stdin, stdout, stderr = ssh.exec_command(f"python3 /path/to/remote_server.py {remote_video_path}")
        stderr_output = stderr.read().decode()
        if stderr_output:
            logging.error(f"Error in remote chunking: {stderr_output}")
            return None

        chunk_files = stdout.read().decode().split()
        for chunk_file in chunk_files:
            chunk_file_name = os.path.basename(chunk_file)
            scp = SCPClient(ssh.get_transport())
            scp.get(chunk_file, os.path.join(local_chunks_path, chunk_file_name))
            scp.close()

        logging.info(f"Completed transfer of chunks for {video_name}")
        return local_chunks_path
    except Exception as e:
        logging.error(f"Error retrieving video chunks: {str(e)}")
        return None
    finally:
        ssh.close()


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


def transfer_remaining_chunks(current_ip, chunks):
    global total_data_sent_to_satellites
    node_ips = list(NODES.values())
    current_index = node_ips.index(current_ip)
    next_index = (current_index + 1) % len(node_ips)
    next_ip = node_ips[next_index]

    logging.info(f"Transferring remaining chunks to {next_ip}")

    ssh = create_ssh_client(next_ip, 22, 'satellite_user', 'satellite_password')
    scp = SCPClient(ssh.get_transport())

    for index in chunks:
        local_chunk_path = f"{LOCAL_CACHE_PATH}/chunk_{index:03d}"
        with open(local_chunk_path, 'rb') as f:
            chunk = f.read()
        scp.put(local_chunk_path, f'/path/on/satellite/chunk_{index:03d}')
        total_data_sent_to_satellites += len(chunk)
        os.remove(local_chunk_path)

    scp.close()
    ssh.close()


@app.route('/get_chunk', methods=['GET'])
def get_chunk():
    global download_count, total_response_time_with_cache, total_response_time_without_cache, cache_hits, \
        cache_misses, total_data_sent_to_clients, total_data_sent_to_satellites
    url = request.args.get('url')
    chunk_index = request.args.get('index', type=int)
    if not url or chunk_index is None:
        return jsonify({"error": "No URL or chunk index provided"}), 400

    start_time = time.time()
    cached_chunks_path = lru_cache.get(url)
    if cached_chunks_path:
        chunk_path = os.path.join(cached_chunks_path, f"chunk_{chunk_index:03d}")
        if os.path.exists(chunk_path):
            cache_hits += 1
            with open(chunk_path, 'rb') as f:
                chunk = f.read()
            total_response_time_with_cache += (time.time() - start_time)
            total_data_sent_to_clients += len(chunk)
            return jsonify({"message": "Chunk is in cache", "chunk": chunk, "from_cache": True}), 200

    cache_misses += 1
    chunks_path = get_video_chunks_from_remote_storage(url)

    if chunks_path is None:
        total_response_time_without_cache += (time.time() - start_time)
        return jsonify({"error": "Chunks not found in remote storage"}), 404

    chunks = [open(os.path.join(chunks_path, f), 'rb').read() for f in sorted(os.listdir(chunks_path))]
    distribution = distribute_chunks(chunks)
    save_metadata(url, distribution)
    lru_cache.put(url, chunks_path)
    download_count += 1

    current_ip = request.remote_addr
    if current_ip not in distribution:
        transfer_remaining_chunks(current_ip, distribution[current_ip])

    for ip, chunk_indices in distribution.items():
        if ip != current_ip:
            ssh = create_ssh_client(ip, 22, 'satellite_user', 'satellite_password')
            scp = SCPClient(ssh.get_transport())
            for index in chunk_indices:
                local_chunk_path = f"{chunks_path}/chunk_{index:03d}"
                with open(local_chunk_path, 'rb') as f:
                    chunk = f.read()
                scp.put(local_chunk_path, f'/path/on/satellite/chunk_{index:03d}')
                total_data_sent_to_satellites += len(chunk)
                os.remove(local_chunk_path)
            scp.close()
            ssh.close()

    chunk_path = os.path.join(chunks_path, f"chunk_{chunk_index:03d}")
    with open(chunk_path, 'rb') as f:
        chunk = f.read()

    total_response_time_without_cache += (time.time() - start_time)
    total_data_sent_to_clients += len(chunk)

    satellite = None
    for name, timestamp_str in HANDOFF.items():
        timestamp = datetime.fromisoformat(timestamp_str)
        if timestamp <= datetime.now():
            satellite = timestamp_str
            break

    return jsonify({
        "message": "Chunk retrieved from remote storage",
        "chunk": chunk,
        "from_cache": False,
        "satellite_handoff": satellite
    }), 200


@app.route('/metrics', methods=['GET'])
def get_metrics():
    return jsonify({
        "download_count": download_count,
        "total_response_time_with_cache": total_response_time_with_cache,
        "total_response_time_without_cache": total_response_time_without_cache,
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "total_data_sent_to_satellites": total_data_sent_to_satellites,
        "total_data_sent_to_clients": total_data_sent_to_clients
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=9000)
