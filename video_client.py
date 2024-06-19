import requests


def request_video(url):
    try:
        response = requests.get(f'http://<cache_server_address>/get_video', params={'url': url})
        response.raise_for_status()
        data = response.json()
        if 'video_file' in data:
            print(f"Video file: {data['video_file']}")
        print(data['message'])
    except requests.RequestException as e:
        print(f"Error requesting video: {e}")


def main():
    urls = [
        "video urls"
    ]

    for url in urls:
        print(f"Requesting video from {url}...")
        request_video(url)


if __name__ == "__main__":
    main()
