import requests
import re
import os

# 配置源地址
API_URL = "https://api.github.com/repos/MetaCubeX/meta-rules-dat/contents/geo/geosite?ref=meta"
RAW_URL = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/"

def get_file_list():
    """获取所有 .list 文件名"""
    r = requests.get(API_URL)
    if r.status_code == 200:
        return [f['name'] for f in r.json() if f['name'].endswith('.list')]
    return []

def classify_logic():
    files = get_file_list()
    domestic_set = set()
    oversea_set = set()

    # 1. 先抓取明确的海外基准包，用于后续比对排他
    print("Fetching overseabase...")
    oversea_base_resp = requests.get(RAW_URL + "geolocation-!cn.list")
    oversea_base = set(oversea_base_resp.text.splitlines()) if oversea_base_resp.status_code == 200 else set()

    # 2. 遍历所有文件
    for name in files:
        print(f"Processing: {name}")
        r = requests.get(RAW_URL + name)
        if r.status_code != 200: continue
        
        # 清洗域名：过滤注释和空行
        content = [l.strip() for l in r.text.splitlines() if l.strip() and not l.startswith('#')]
        
        # --- 判定逻辑 ---
        # A. 明确的海外特征：文件名含 !cn, gfw, 或内容在 oversea_base 中占比高
        is_oversea = False
        if "!cn" in name or "gfw" in name or "greatfire" in name:
            is_oversea = True
        elif any(kw in name.lower() for kw in ["google", "youtube", "netflix", "telegram", "twitter", "facebook"]):
            is_oversea = True
        
        # B. 默认策略：除明确海外名外，其余全归 Domestic (包含 51job, 4399 等)
        if is_oversea:
            oversea_set.update(content)
        else:
            domestic_set.update(content)

    # 3. 写入文件 (SmartDNS 兼容格式)
    with open("domestic_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("# Generated Domestic Domains\n" + "\n".join(sorted(list(domestic_set))))
        
    with open("oversea_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("# Generated Oversea Domains\n" + "\n".join(sorted(list(oversea_set))))

if __name__ == "__main__":
    classify_logic()
