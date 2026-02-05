import requests
import re
import zipfile
import io
import os

ZIP_URL = "https://github.com/MetaCubeX/meta-rules-dat/archive/refs/heads/meta.zip"

def is_valid_domain(domain):
    if not domain or len(domain) > 253:
        return False
    
    invalid_suffixes = (
        ".arpa", ".local", ".lan", ".home.arpa", ".root", 
        ".invalid", ".test", ".example", ".onion", ".localhost"
    )
    if domain.endswith(invalid_suffixes):
        return False
    
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
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
        "category-ads-all", "global", "outside", "apple-cdn", "apple-itunes",
        "cloudflare", "quad9", "opendns"
    ]

    DNS_FILE_BLACKLIST = ["dns", "doh", "category-dns", "category-pki", "private"]

    for member in z.namelist():
        if "geo/geosite/" in member and member.endswith(".list"):
            filename = os.path.basename(member).lower()
            if any(dk in filename for dk in DNS_FILE_BLACKLIST):
                continue
            
            is_oversea = any(kw in filename for kw in OVERSEA_KEYWORDS)
            if "apple" in filename and "cn" not in filename:
                is_oversea = True
            
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

    force_oversea_kw = ["google", "cloudflare", "quad9", "dns-query"]
    to_move = []
    for d in domestic_set:
        if any(kw in d for kw in force_oversea_kw) or any(x in d for x in ["apple.com", "mzstatic.com", "icloud.com"]):
            to_move.append(d)

    for d in to_move:
        if d in domestic_set:
            domestic_set.remove(d)
            oversea_set.add(d)

    domestic_set = domestic_set - oversea_set

    with open("domestic_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("\n".join(sorted(list(domestic_set))))
        
    with open("oversea_domain_list.conf", "w", encoding='utf-8') as f:
        f.write("\n".join(sorted(list(oversea_set))))

if __name__ == "__main__":
    build()
