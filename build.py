import requests
import re

# 数据源
RAW_URL_PREFIX = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/"
API_URL = "https://api.github.com/repos/MetaCubeX/meta-rules-dat/contents/geo/geosite?ref=meta"

def clean_domain(line):
    """
    清洗格式：将 'domain:google.com' 或 'full:www.baidu.com' 统一提取为 'google.com'
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    # 移除前缀 (domain:, full:, keyword:, regexp:)
    line = re.sub(r'^(domain|full|keyword|regexp):', '', line)
    # 移除所有后缀和注释
    line = line.split(' ')[0].split('\t')[0]
    return line

def get_file_list():
    r = requests.get(API_URL)
    if r.status_code == 200:
        return [f['name'] for f in r.json() if f['name'].endswith('.list')]
    return []

def build():
    files = get_file_list()
    domestic_set = set()
    oversea_set = set()

    # 1. 预加载海外核心判定表 (geolocation-!cn)
    print("Loading Oversea Baseline...")
    base_not_cn = requests.get(RAW_URL_PREFIX + "geolocation-!cn.list").text.splitlines()
    oversea_baseline = {clean_domain(l) for l in base_not_cn if clean_domain(l)}

    # 2. 遍历全量文件
    for name in files:
        print(f"Processing {name}...")
        r = requests.get(RAW_URL_PREFIX + name)
        if r.status_code != 200: continue
        
        lines = r.text.splitlines()
        
        # --- 判定逻辑修正 ---
        # 如果文件名包含 !cn, gfw, netflix 等，或者该文件内的域名在 baseline 中出现过
        is_oversea = False
        if any(kw in name.lower() for kw in ["!cn", "gfw", "greatfire", "proxy", "google", "youtube", "netflix", "telegram"]):
            is_oversea = True
        
        for l in lines:
            domain = clean_domain(l)
            if not domain: continue
            
            # 如果域名本身在海外基准库里，强制划入海外
            if is_oversea or domain in oversea_baseline:
                oversea_set.add(domain)
            else:
                domestic_set.add(domain)

    # 3. 导出结果 (纯域名格式)
    with open("domestic_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("# Generated Pure Domestic Domains\n")
        f.write("\n".join(sorted(list(domestic_set))))
        
    with open("oversea_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("# Generated Pure Oversea Domains\n")
        f.write("\n".join(sorted(list(oversea_set))))

    print(f"Success! Domestic: {len(domestic_set)} | Oversea: {len(oversea_set)}")

if __name__ == "__main__":
    build()
