import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import load_credentials
from src.fetch_data import fetch_jquants_data
from src.preprocessing import preprocessing_data
from src.charts import plot_charts
from src.create_report import create_and_upload_report
from src.notify_LINE import send_report_to_LINE

def main():

    #==========================================================
    ### 1. outputディレクトリの作成
    #==========================================================

    BATCH_ID = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d%H%M%S")
    BASE_DIR = Path(__file__).resolve().parent

    INTERMEDIATE_DIR = BASE_DIR / "intermediate"
    OUTPUT_DIR = BASE_DIR / "output"
    CHARTS_DIR = OUTPUT_DIR / "charts"
    REPORTS_DIR = OUTPUT_DIR / "reports"
    
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    #==========================================================
    ### 2. configファイルの読み込み
    #==========================================================
    
    config_path = f"{BASE_DIR}/input/conf/"
    
    # APIキー等の認証情報（credentials.yml）の読み込み
    # GitHub上にcredentials.ymlはアップロードできないため、GitHub Actionsで定期実行する場合はGithub Actionsのsecret機能を使う
    Path_credentials = Path(config_path + "credentials.yml")
    credentials = load_credentials(Path_credentials)
    
    # その他パラメータの読み込み
    with open(config_path + "parameters.yml", "r") as f:
        params = yaml.safe_load(f)

    # J-Quants API関連
    JQUANTS_API_KEY = credentials["jquants"]["key"]

    jquants_base_url = params["jquants"]["base_url"]
    Path_equities_master = params["jquants"]["paths"]["equities_master"]
    Path_daily_bars = params["jquants"]["paths"]["daily_bars"]
    # Path_fins_summary = params["jquants"]["paths"]["fins_summary"]
    # Path_earnings_calender = params["jquants"]["paths"]["earnings_calender"]
    Path_markets_calender = params["jquants"]["paths"]["markets_calender"]
    # Path_investors_type = params["jquants"]["paths"]["investors_type"]
    # Path_daily_topix = params["jquants"]["paths"]["daily_topix"]

    print(jquants_base_url)

    # LINE Messaging API関連
    LINE_CHANNEL_ACCESS_TOKEN = credentials["LINE_official_account"]["channel_access_token"]

    line_base_url = params["LINE"]["base_url"]
    Path_broadcast = params["LINE"]["paths"]["broadcast"]

    print(line_base_url)
    
    # Cloudflare R2 API関連
    CLOUDFLARE_ACCOUNT_ID = credentials["cloudflare"]["account_id"]
    R2_ACCESS_KEY_ID = credentials["cloudflare"]["r2"]["access_key_id"]
    R2_SECRET_ACCESS_KEY = credentials["cloudflare"]["r2"]["secret_access_key"]
    r2_public_dev_id = credentials["cloudflare"]["r2"]["public_dev_id"]
    
    r2_public_dev_url = params["cloudflare"]["r2"]["public_dev_url"]
    r2_public_dev_url = r2_public_dev_url.replace("{public_dev_id}", r2_public_dev_id)
    
    r2_bucket_name = params["cloudflare"]["r2"]["backet_name"]
    r2_report_folder_name = params["cloudflare"]["r2"]["paths"]["new_high_report"]
    r2_preprocessed_table_folder_name = params["cloudflare"]["r2"]["paths"]["preprocessed_table"]
    

    print("configファイルの読み込み【完了】")
    
    #==========================================================
    ### 3. API呼び出し・データ取得 
    #==========================================================
           
    newest_market_date, market_date_last_365days, equities_master, daily_stock_df = fetch_jquants_data(
        JQUANTS_API_KEY,
        jquants_base_url,
        Path_markets_calender,
        Path_equities_master,
        Path_daily_bars
    )

    # daily_stock_df.to_parquet(f"{INTERMEDIATE_DIR} / daily_stock_data_365days_{newest_market_date}.parquet")
    # daily_stock_df = pd.read_parquet(f"{INTERMEDIATE_DIR} / daily_stock_data_365days_{newest_market_date}.parquet")
    
    print("API呼び出し・データ取得 【完了】")
    
    #==========================================================
    ### 4. Preprocessing
    #==========================================================
    
    new_highs_df, new_highs_list = preprocessing_data(
        newest_market_date, 
        market_date_last_365days, 
        equities_master, 
        daily_stock_df,
        INTERMEDIATE_DIR,
        BATCH_ID,
        r2_preprocessed_table_folder_name,
        CLOUDFLARE_ACCOUNT_ID,
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        r2_public_dev_url,
        r2_bucket_name
    )
    
    print("Preprocessing 【完了】")

    #==========================================================
    ### 5. チャート作成
    #==========================================================
    
    plot_charts(daily_stock_df, new_highs_list, CHARTS_DIR)
    
    print("チャート作成 【完了】")
    
    #==========================================================
    ### 6. レポート作成＆アップロード
    #==========================================================

    Path_report_template = f"{BASE_DIR}/input/report_templates"
    file_name_report_template = "new_high_report.html"
    
    Path_output_report_html = f"{REPORTS_DIR}/new_high_report_{newest_market_date}.html"
    Path_output_report_pdf = f"{REPORTS_DIR}/new_high_report_{newest_market_date}.pdf"
    
    report_url = create_and_upload_report(
        newest_market_date, 
        new_highs_df, 
        Path_report_template, 
        file_name_report_template, 
        Path_output_report_html, 
        Path_output_report_pdf,
        BATCH_ID,
        CLOUDFLARE_ACCOUNT_ID,
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        r2_public_dev_url,
        r2_bucket_name,
        r2_report_folder_name
    )
    
    print("レポート作成＆アップロード 【完了】")

    #==========================================================
    ### 7. LINEで通知
    #==========================================================

    send_report_to_LINE(
        new_highs_df, 
        newest_market_date, 
        report_url, 
        LINE_CHANNEL_ACCESS_TOKEN, 
        line_base_url, 
        Path_broadcast
    )
    
    print("LINEで通知 【完了】")

if __name__ == "__main__":
    main()
