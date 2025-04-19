#!/usr/bin/env python3
import argparse, subprocess, boto3, requests
from botocore.exceptions import ClientError

# ----------- S3 ENUM ------------
def scan_s3(bucket_list):
    print("\n[+] Escaneando buckets S3...")
    with open(bucket_list, "r") as f:
        for bucket in f:
            bucket = bucket.strip()
            try:
                s3 = boto3.client('s3')
                result = s3.list_objects_v2(Bucket=bucket)
                if 'Contents' in result:
                    print(f"[FOUND] {bucket} - público y contiene archivos.")
            except ClientError as e:
                if e.response['Error']['Code'] == "AccessDenied":
                    print(f"[DENIED] {bucket} - existe pero no público.")
                elif e.response['Error']['Code'] == "NoSuchBucket":
                    pass
                else:
                    print(f"[ERROR] {bucket}: {e}")

# ----------- Cognito ENUM ------------
def check_cognito(endpoint):
    print(f"\n[+] Probando enumeración básica contra Cognito: {endpoint}")
    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.ListUsers"
    }
    payload = '{"UserPoolId":"FAKE-ID"}'
    try:
        res = requests.post(endpoint, data=payload, headers=headers)
        print(f"[+] Status: {res.status_code} | {res.text[:100]}")
    except Exception as e:
        print(f"[!] Error contactando Cognito: {e}")

# ----------- API Gateway Fuzzer ------------
def fuzz_api(base_url, wordlist):
    print(f"\n[+] Fuzzing API Gateway en {base_url}...")
    with open(wordlist, 'r') as f:
        for path in f:
            url = base_url.rstrip("/") + "/" + path.strip()
            try:
                res = requests.get(url, timeout=3)
                print(f"[{res.status_code}] {url}")
            except:
                pass

# ----------- CloudFront fingerprinting ------------
def fingerprint_cloudfront(url):
    print(f"\n[+] Fingerprinting CloudFront en {url}...")
    try:
        res = requests.get(url, timeout=5)
        headers = res.headers
        for h in headers:
            if "cloudfront" in headers[h].lower():
                print(f"[+] CloudFront detectado en header: {h}: {headers[h]}")
    except Exception as e:
        print(f"[!] Error al consultar {url}: {e}")

# ----------- MAIN ------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AWS Offensive Recon Toolkit")
    parser.add_argument("--s3", help="Wordlist para buckets S3")
    parser.add_argument("--cognito", help="Endpoint de Cognito (ej: https://cognito-idp.eu-west-1.amazonaws.com/)")
    parser.add_argument("--api", help="URL base para fuzzing (ej: https://api.target.com)")
    parser.add_argument("--api-wordlist", help="Wordlist para fuzzing de endpoints")
    parser.add_argument("--cloudfront", help="URL pública protegida con CloudFront")

    args = parser.parse_args()

    if args.s3:
        scan_s3(args.s3)

    if args.cognito:
        check_cognito(args.cognito)

    if args.api and args.api_wordlist:
        fuzz_api(args.api, args.api_wordlist)

    if args.cloudfront:
        fingerprint_cloudfront(args.cloudfront)
