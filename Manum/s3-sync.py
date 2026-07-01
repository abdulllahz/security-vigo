import os
import boto3
import logging
import argparse
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

def get_prefix(path):
    today = datetime.now(timezone.utc)
    return f"{path}/{today:%Y/%m/%d}/"

def sync(s3, bucket, prefix, local_dir):
    paginator = s3.get_paginator("list_objects_v2")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
    downloaded = 0
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"] < cutoff:
                continue
            key = obj["Key"]
            relative = key[len(prefix):]
            if not relative:
                continue
            local_path = os.path.join(local_dir, relative)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            if os.path.exists(local_path):
                local_mtime = datetime.fromtimestamp(os.path.getmtime(local_path)).replace(tzinfo=obj["LastModified"].tzinfo)
                if local_mtime >= obj["LastModified"] and os.path.getsize(local_path) == obj["Size"]:
                    continue
            log.info("Downloading %s", key)
            s3.download_file(bucket, key, local_path)
            downloaded += 1
    deleted = 0
    for root, _, files in os.walk(local_dir):
        for fname in files:
            local_path = os.path.join(root, fname)
            mtime = datetime.fromtimestamp(os.path.getmtime(local_path), tz=timezone.utc)
            if mtime < cutoff:
                os.remove(local_path)
                log.info("Deleted stale file %s", local_path)
                deleted += 1
    log.info("Sync complete — %d file(s) downloaded, %d file(s) deleted", downloaded, deleted)

def main():
    parser = argparse.ArgumentParser(description='Get My Logs!')
    parser.add_argument('-p', '--path', type=str, help='path', default=0)
    parser.add_argument('-s', '--s3', type=str, help='bucket', default=0)
    parser.add_argument('-o', '--output', type=str, help='output directory', default=0)
    args = parser.parse_args()
    s3 = boto3.client("s3")
    os.makedirs(args.output, exist_ok=True)
    prefix = get_prefix(args.path)
    log.info("Starting sync from s3://%s/%s",args.s3,prefix)
    try:
        sync(s3, args.s3, prefix,args.output)
    except Exception as e:
        log.error("Sync failed: %s",e)
        raise SystemExit(1)

if __name__ == "__main__":
    main()