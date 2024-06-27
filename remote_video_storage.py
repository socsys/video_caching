import os
import sys

CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB


def chunk_video(video_path):
    chunks_dir = video_path + "_chunks"
    if not os.path.exists(chunks_dir):
        os.makedirs(chunks_dir)

    with open(video_path, 'rb') as f:
        chunk_num = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunk_path = os.path.join(chunks_dir, f"chunk_{chunk_num:03d}")
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk)
            print(chunk_path)
            chunk_num += 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 remote_video_chunker.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    chunk_video(video_path)
