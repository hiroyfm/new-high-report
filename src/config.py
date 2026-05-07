import os
import yaml
from pathlib import Path


def load_credentials(Path_credentials):
    ### credentials.ymlの読み込み
    ### GitHub上にcredentials.ymlはアップロードできないため、GitHub Actionsで定期実行する場合はGithub Actionsのsecret機能を使う

    # ローカル実行の場合
    if Path_credentials.exists():
        with open(Path_credentials, encoding="utf-8") as f:
            return yaml.safe_load(f)

    # GitHub Actionsで定期実行する場合
    return {
        "jquants": {
            "key": os.environ["JQUANTS_API_KEY"],
        },
        
        "LINE_official_account": {
            "channel_access_token": os.environ["LINE_CHANNEL_ACCESS_TOKEN"],
        },

        "cloudflare": {
            "account_id": os.environ["CLOUDFLARE_ACCOUNT_ID"],

            "r2": {
                "access_key_id": os.environ["R2_ACCESS_KEY_ID"],
                "secret_access_key": os.environ["R2_SECRET_ACCESS_KEY"],
                "public_dev_id": os.environ["R2_PUBLIC_DEV_ID"],
            }
        }
    }