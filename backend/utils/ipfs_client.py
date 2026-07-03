import os
import json
import hashlib
from typing import Dict, Tuple
from backend.config import get_settings


async def upload_metadata_to_ipfs(metadata: Dict) -> Tuple[str, str]:
    settings = get_settings()
    
    if settings.pinata_api_key and settings.pinata_secret_key:
        try:
            import httpx
            url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
            headers = {
                "pinata_api_key": settings.pinata_api_key,
                "pinata_secret_api_key": settings.pinata_secret_key,
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=metadata, headers=headers, timeout=10.0)
                if res.status_code == 200:
                    ipfs_hash = res.json()["IpfsHash"]
                    return ipfs_hash, f"{settings.ipfs_gateway}{ipfs_hash}"
        except Exception:
            pass

    serialized = json.dumps(metadata, sort_keys=True)
    ipfs_hash = f"Qm{hashlib.sha256(serialized.encode()).hexdigest()[:44]}"
    metadata_uri = f"{settings.ipfs_gateway}{ipfs_hash}"
    
    os.makedirs("./data/ipfs_cache", exist_ok=True)
    with open(f"./data/ipfs_cache/{ipfs_hash}.json", "w") as f:
        json.dump(metadata, f, indent=2)

    return ipfs_hash, metadata_uri
