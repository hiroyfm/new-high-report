from datetime import date, datetime, timedelta
import requests
import pandas as pd
import time
from joblib import Parallel, delayed

def fetch_market_date(JQUANTS_API_KEY, jquants_base_url, Path_markets_calender):
    headers = {"x-api-key": JQUANTS_API_KEY}

    today = date.today()
    from_ = today - timedelta(days=400)
    to = today

    api_call_params = {}
    api_call_params["from"] = from_
    api_call_params["to"] = to
    
    ### 最新の営業日を取得
    res = requests.get(jquants_base_url + Path_markets_calender, params=api_call_params, headers=headers)
    if res.status_code == 200:
        d = res.json()
        data = d["data"]
        while "pagination_key" in d:
            api_call_params["pagination_key"] = d["pagination_key"]
            res = requests.get(jquants_base_url + Path_markets_calender, params=api_call_params, headers=headers)
            d = res.json()
            data += d["data"]
        df = pd.DataFrame(data)
    else:
        print(res.json())
    
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    market_date_last_400days = df[(df["Date"] <= today) & (df["HolDiv"] == "1")]["Date"]
    newest_market_date = max(market_date_last_400days)

    # 最新の営業日から数えて直近1年の営業日を取得
    market_date_last_365days = list(market_date_last_400days[market_date_last_400days >= newest_market_date - timedelta(days=365)])

    return newest_market_date, market_date_last_365days

def fetch_equities_master(JQUANTS_API_KEY, jquants_base_url, Path_equities_master, newest_market_date):
    ### 直近の営業日の上場銘柄一覧を取得
    headers = {"x-api-key": JQUANTS_API_KEY}
    
    api_call_params = {}
    api_call_params["date"] = newest_market_date

    res = requests.get(jquants_base_url + Path_equities_master, params=api_call_params, headers=headers)
    if res.status_code == 200:
        d = res.json()
        data = d["data"]
        while "pagination_key" in d:
            api_call_params["pagination_key"] = d["pagination_key"]
            res = requests.get(jquants_base_url + Path_equities_master, params=api_call_params, headers=headers)
            d = res.json()
            data += d["data"]
        equities_master = pd.DataFrame(data)
    else:
        print(res.json())

    return equities_master

def fetch_daily_stock_data(JQUANTS_API_KEY, jquants_base_url, Path_daily_bars, market_date_last_365days):
    ### 直近1年の全銘柄の日別株価データを取得
    def get_daily_stock_data(date):
        
        print(f"start {date}")
        
        api_call_params = {}
        api_call_params["date"] = date

        # 銘柄×日別の株価四本値データ取得
        res = requests.get(jquants_base_url + Path_daily_bars, params=api_call_params, headers=headers)

        if res.status_code == 200:
            d = res.json()
            extracted_data = d["data"]
            while "pagination_key" in d:
                api_call_params["pagination_key"] = d["pagination_key"]
                res = requests.get(jquants_base_url + Path_daily_bars, params=api_call_params, headers=headers)
                d = res.json()
                extracted_data += d["data"]
            
        elif res.status_code == 429:
            wait = int(res.headers.get("Retry-After", 60))
            print(f"Rate limit. Sleeping {wait} seconds...")
            time.sleep(wait)
            
        else:
            print(res.status_code)
            print(res.json())
            
        return extracted_data

    headers = {"x-api-key": JQUANTS_API_KEY}

    # 全銘柄の過去1年の日別株価データを1日ずつ取得（joblibで2コア並列処理）
    daily_stock_data = Parallel(n_jobs=2)(
        delayed(get_daily_stock_data)(date) for date in market_date_last_365days
    )

    # 取得したデータを整形
    daily_stock_df = pd.concat(
    (
        pd.DataFrame(trial_result)
        for trial_result in daily_stock_data
    ),
    ignore_index=True
    )
    
    return daily_stock_df

def fetch_jquants_data(
    JQUANTS_API_KEY,
    jquants_base_url,
    Path_markets_calender,
    Path_equities_master,
    Path_daily_bars
):
    # 直近営業日と、直近営業日を基準とした過去1年の市場営業日を取得
    newest_market_date, market_date_last_365days = fetch_market_date(JQUANTS_API_KEY, jquants_base_url, Path_markets_calender)
    
    # 直近営業日の上場銘柄一覧を取得
    equities_master = fetch_equities_master(JQUANTS_API_KEY, jquants_base_url, Path_equities_master, newest_market_date)
    
    # 直近営業日を基準とした直近1年の全銘柄の日別株価データを取得
    daily_stock_df = fetch_daily_stock_data(JQUANTS_API_KEY, jquants_base_url, Path_daily_bars, market_date_last_365days)
      
    return newest_market_date, market_date_last_365days, equities_master, daily_stock_df