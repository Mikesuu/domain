import requests
import re

RAW_URL_PREFIX = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/"
API_URL = "https://api.github.com/repos/MetaCubeX/meta-rules-dat/contents/geo/geosite?ref=meta"

def clean_domain(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    line = re.sub(r'^(domain|full|keyword|regexp):', '', line)
    line = re.sub(r'^(\+\.|\.)', '', line)
    line = line.split(' ')[0].split('\t')[0]
    if re.search(r'[\\*?|]', line):
        return None
    return line.lower()

def build():
    r = requests.get(API_URL)
    if r.status_code != 200:
        return
    
    files = [f['name'] for f in r.json() if f['name'].endswith('.list')]
    domestic_set = set()
    oversea_set = set()

    OVERSEA_KEYWORDS = [
        "!cn", "gfw", "greatfire", "google", "youtube", "netflix", 
        "telegram", "facebook", "twitter", "instagram", "proxy",
        "category-ads-all"
    ]

    for name in files:
        resp = requests.get(RAW_URL_PREFIX + name)
        if resp.status_code != 200: continue
        
        is_oversea = any(kw in name.lower() for kw in OVERSEA_KEYWORDS)
        
        for line in resp.text.splitlines():
            domain = clean_domain(line)
            if domain:
                if is_oversea:
                    oversea_set.add(domain)
                else:
                    domestic_set.add(domain)

    domestic_set = domestic_set - oversea_set

    with open("domestic_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("\n".join(sorted(list(domestic_set))))
        
    with open("oversea_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("\n".join(sorted(list(oversea_set))))

if __name__ == "__main__":
    build()
