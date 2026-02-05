import requests
import re
import zipfile
import io
import os

ZIP_URL = "https://github.com/MetaCubeX/meta-rules-dat/archive/refs/heads/meta.zip"

def is_valid_domain(domain):
    if not domain or len(domain) > 253:
        return False
    if not re.match(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$", domain):
        return False
    return True

def clean_domain(line):
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    line = re.sub(r'^(domain|full|keyword|regexp):', '', line)
    line = re.sub(r'^(\+\.|\.)', '', line)
    line = line.split(' ')[0].split('\t')[0]
    domain = line.lower()
    if is_valid_domain(domain):
        return domain
    return None

def build():
    r = requests.get(ZIP_URL)
    if r.status_code != 200:
        return
    
    z = zipfile.ZipFile(io.BytesIO(r.content))
    domestic_set = set()
    oversea_set = set()

    OVERSEA_KEYWORDS = [
        "!cn", "gfw", "greatfire", "google", "youtube", "netflix", 
        "telegram", "facebook", "twitter", "instagram", "proxy",
        "category-ads-all", "global", "outside"
    ]

    for member in z.namelist():
        if "geo/geosite/" in member and member.endswith(".list"):
            filename = os.path.basename(member)
            is_oversea = any(kw in filename.lower() for kw in OVERSEA_KEYWORDS)
            
            with z.open(member) as f:
                try:
                    content = f.read().decode('utf-8')
                    for line in content.splitlines():
                        domain = clean_domain(line)
                        if domain:
                            if is_oversea:
                                oversea_set.add(domain)
                            else:
                                domestic_set.add(domain)
                except:
                    continue

    domestic_set = domestic_set - oversea_set

    with open("domestic_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("\n".join(sorted(list(domestic_set))))
        
    with open("oversea_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("\n".join(sorted(list(oversea_set))))

if __name__ == "__main__":
    build()
