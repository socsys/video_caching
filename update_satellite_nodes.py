# import json
# import os
# import glob
# from datetime import datetime
#
#
# def extract_satellite_info(file_path):
#     with open(file_path, 'r') as f:
#         data = json.load(f)
#     for item in data:
#         if item['end1'] == 'LHR':
#             return item['end2']
#     return None
#
#
# def get_ip_for_satellite(constellation_file, satellite_name):
#     print("constellation file path:", constellation_file)
#     with open(constellation_file, 'r') as f:
#         data = json.load(f)
#     lhr_data = {key: value for key, value in data.items() if key.startswith('LHR')}
#     # Extract the IP address from the key that starts with 'LHR'
#     lhr_ip = next((value for key, value in data.items() if key.startswith('LHR')), None)
#     new_ip = ""
#     if lhr_ip:
#         ip_parts = lhr_ip.split('.')
#         ip_parts[-1] = str(int(ip_parts[-1]) + 1)
#         new_ip = '.'.join(ip_parts)
#         print(new_ip)
#     else:
#         print("No IP address found starting with 'LHR'")
#
#     # return lhr_ip
#     return new_ip
#
#
# def update_nodes():
#     gsl_files = sorted(glob.glob('../results_hotnets_20231113_103000/gsl_latency_bw_*.json'))
#     constellation_files = sorted(glob.glob('../results_hotnets_20231113_103000/constellation_ip_addresses_*.json'))
#     nodes = {}
#
#     for gsl_file, constellation_file in zip(gsl_files, constellation_files):
#         satellite_name = extract_satellite_info(gsl_file)
#         if satellite_name:
#             ip = get_ip_for_satellite(constellation_file, satellite_name)
#             if ip:
#                 nodes[satellite_name] = ip
#
#     with open('nodes.json', 'w') as f:
#         json.dump(nodes, f, indent=2)
#
#
# if __name__ == "__main__":
#     update_nodes()


import json
import glob
from datetime import datetime


def extract_satellite_info(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    for item in data:
        if item['end1'] == 'LHR':
            return item['end2']
    return None


def get_ip_for_satellite(constellation_file, satellite_name):
    with open(constellation_file, 'r') as f:
        data = json.load(f)
    lhr_data = {key: value for key, value in data.items() if key.startswith('LHR')}
    lhr_ip = next((value for key, value in data.items() if key.startswith('LHR')), None)
    new_ip = ""
    if lhr_ip:
        ip_parts = lhr_ip.split('.')
        ip_parts[-1] = str(int(ip_parts[-1]) + 1)
        new_ip = '.'.join(ip_parts)
    return new_ip


def update_nodes():
    gsl_files = sorted(glob.glob('../results_hotnets_20231113_103000/gsl_latency_bw_*.json'))
    constellation_files = sorted(glob.glob('../results_hotnets_20231113_103000/constellation_ip_addresses_*.json'))
    nodes = {}
    handoff = {}

    for gsl_file, constellation_file in zip(gsl_files, constellation_files):
        satellite_name = extract_satellite_info(gsl_file)
        if satellite_name:
            ip = get_ip_for_satellite(constellation_file, satellite_name)
            if ip:
                shit = f"{gsl_file.split('_')[-2]}_{gsl_file.split('_')[-1].split('.')[0]}"
                nodes[satellite_name] = ip
                timestamp = datetime.strptime(shit, '%Y%m%d_%H%M%S')
                handoff[satellite_name] = timestamp.isoformat()

    with open('nodes.json', 'w') as f:
        json.dump(nodes, f, indent=2)

    with open('handoff.json', 'w') as f:
        json.dump(handoff, f, indent=2)


if __name__ == "__main__":
    update_nodes()
