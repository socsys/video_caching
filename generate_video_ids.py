import random
import string


def generate_video_ids(n=1000):
    video_ids = [''.join(random.choices(string.ascii_letters + string.digits, k=10)) for _ in range(n)]
    with open('video_ids.txt', 'w') as f:
        for video_id in video_ids:
            f.write(video_id + '\n')


generate_video_ids()
