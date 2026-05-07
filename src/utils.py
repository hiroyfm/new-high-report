from pathlib import Path
import boto3


def upload_file_to_cloudflare(
    local_file_path,
    content_type,
    BATCH_ID,
    folder_name,
    CLOUDFLARE_ACCOUNT_ID,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    r2_public_dev_url,
    r2_bucket_name,
):
    """
    Cloudflare R2へファイルをアップロードし、
    公開URLを返す
    """

    local_file_path = Path(local_file_path)

    if not local_file_path.exists():
        raise FileNotFoundError(
            f"ファイルが見つかりません: {local_file_path}"
        )

    object_key = (
        f"{BATCH_ID}/{folder_name}/{local_file_path.name}"
    )

    s3 = boto3.client(
        "s3",
        endpoint_url=(
            f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com"
        ),
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )

    s3.upload_file(
        Filename=str(local_file_path),
        Bucket=r2_bucket_name,
        Key=object_key,
        ExtraArgs={
            "ContentType": content_type,
        },
    )

    public_url = (
        f"{r2_public_dev_url}/{object_key}"
    )

    return public_url