import pandas as pd
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from src.utils import upload_file_to_cloudflare

def extract_new_highs(newest_market_date, equities_master, daily_stock_df):
    ### 直近営業日で52週高値を更新した銘柄を抽出
    daily_stock_df["Date"] = pd.to_datetime(daily_stock_df["Date"], format="%Y-%m-%d").dt.date

    newest_market_date_stock_df = daily_stock_df[["Date", "Code", "AdjH", "AdjC"]][daily_stock_df["Date"] == newest_market_date].reset_index(drop=True)

    high_365days_df = (
        daily_stock_df[["Date", "Code", "AdjH"]].groupby("Code")["AdjH"]
        .max()
        .reset_index()
        .rename(columns={"AdjH": "highest_365days"})
    )

    merged_df = pd.merge(
        newest_market_date_stock_df,
        high_365days_df,
        how="left",
        on="Code"
    )
    new_highs_df = merged_df[merged_df["AdjH"] == merged_df["highest_365days"]].reset_index(drop=True)
    new_highs_df = pd.merge(
        new_highs_df,
        equities_master[["Code", "CoName", "S17Nm", "MktNm"]],
        how="left",
        on="Code"
    )
    
    return new_highs_df

def get_previous_date(newest_market_date, market_date_last_365days):
    ### 直近営業日から1日前、1週間前、1か月前の営業日を取得。該当日が休業日の場合は、該当日より前の最新営業日を取得
    date_1_matket_day_ago = max([date for date in market_date_last_365days if date <= newest_market_date - timedelta(days=1)])
    date_1_matket_week_ago = max([date for date in market_date_last_365days if date <= newest_market_date - timedelta(weeks=1)])
    date_1_matket_month_ago = max([date for date in market_date_last_365days if date <= newest_market_date - relativedelta(months=1)])

    return date_1_matket_day_ago, date_1_matket_week_ago, date_1_matket_month_ago

def filter_date_stock_data(daily_stock_df, date, period):
    return (
        daily_stock_df[daily_stock_df["Date"] == date][["Code", "AdjC"]]
        .rename(columns={"AdjC":f"AdjC_1{period}_ago"})
        .reset_index(drop=True)
    )

def calculate_growth_rate(new_highs_df, daily_stock_df_1day_ago, daily_stock_df_1week_ago, daily_stock_df_1month_ago):
    ### 新高値更新銘柄テーブルに、1日前、1週間前、1か月前の株価終値を追加し、伸び率を計算
    new_highs_df = pd.merge(new_highs_df, daily_stock_df_1day_ago, how="left", on="Code")
    new_highs_df = pd.merge(new_highs_df, daily_stock_df_1week_ago, how="left", on="Code")
    new_highs_df = pd.merge(new_highs_df, daily_stock_df_1month_ago, how="left", on="Code")

    new_highs_df["Growth_rate_1day"] = (new_highs_df["AdjC"] / new_highs_df["AdjC_1day_ago"]) * 100 - 100
    new_highs_df["Growth_rate_1week"] = (new_highs_df["AdjC"] / new_highs_df["AdjC_1week_ago"]) * 100 - 100
    new_highs_df["Growth_rate_1month"] = (new_highs_df["AdjC"] / new_highs_df["AdjC_1month_ago"]) * 100 - 100
    
    return new_highs_df

def preprocessing_data(
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
    r2_bucket_name,
):
    
    # 直近の営業日で​52週高値を​更新した​銘柄を​抽出
    new_highs_df = extract_new_highs(newest_market_date, equities_master, daily_stock_df)
    
    # 直近の​営業日の​1日前、​1週間前、​1か​月前の​営業日を​取得
    # ※該当日が​休業日の​場合は、​該当日より​前の​最新営業日を​取得
    date_1_matket_day_ago, date_1_matket_week_ago, date_1_matket_month_ago = get_previous_date(newest_market_date, market_date_last_365days)
    
    # 直近営業日の​1日前、​1週間前、​1か​月前の​営業日の​全銘柄の​株価終値データを​取得
    daily_stock_df_1day_ago = filter_date_stock_data(daily_stock_df, date_1_matket_day_ago, "day")
    daily_stock_df_1week_ago = filter_date_stock_data(daily_stock_df, date_1_matket_week_ago, "week")
    daily_stock_df_1month_ago = filter_date_stock_data(daily_stock_df, date_1_matket_month_ago, "month")
    
    # 直近​営業日で​52週高値を​更新した​銘柄に​1日前、​1週間前、​1か​月前の​株価終値を​追加し、​伸び率を​計算
    new_highs_df = calculate_growth_rate(new_highs_df, daily_stock_df_1day_ago, daily_stock_df_1week_ago, daily_stock_df_1month_ago)
    
    # 3市場のみに限定
    target_Mkt = ["プライム", "スタンダード", "グロース"]
    new_highs_df = new_highs_df[new_highs_df["MktNm"].isin(target_Mkt)]

    # カラム順と表示順の調整
    cat_cols = ["Date", "Code", "CoName", "S17Nm", "MktNm"]
    num_cols = ["AdjH", "AdjC", "AdjC_1day_ago", "Growth_rate_1day", "AdjC_1week_ago", "Growth_rate_1week", "AdjC_1month_ago", "Growth_rate_1month"]
    new_highs_df = new_highs_df[cat_cols + num_cols].sort_values(by=["Growth_rate_1month"], ascending=[False]).reset_index(drop=True)

    # 新高値更新銘柄リストも作成
    new_highs_list = list(new_highs_df["Code"].unique())
    
    # 加工済みデータを中間テーブルとしてParquetで保存
    Path_new_highs_df = INTERMEDIATE_DIR / f"new_highs_df_{newest_market_date}.parquet"
    new_highs_df.to_parquet(Path_new_highs_df)
    
    # 加工済みのParquetをCloudflareにアップロード
    content_type="application/octet-stream"  
    
    _ = upload_file_to_cloudflare(
        Path_new_highs_df,
        content_type,
        BATCH_ID,
        r2_preprocessed_table_folder_name,
        CLOUDFLARE_ACCOUNT_ID,
        R2_ACCESS_KEY_ID,
        R2_SECRET_ACCESS_KEY,
        r2_public_dev_url,
        r2_bucket_name,
    )
 
    return new_highs_df, new_highs_list
    