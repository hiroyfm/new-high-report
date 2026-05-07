from joblib import Parallel, delayed
import matplotlib.pyplot as plt
import pandas as pd

def save_price_chart(df, output_path):
    ### 新高値更新銘柄の52週チャートを出力
    plt.figure(figsize=(8, 4))
    plt.plot(df["Date"], df["AdjC"])
    plt.title("Stock Price Chart")
    plt.xlabel("Date")
    plt.ylabel("Stock Price")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

def plot_charts(daily_stock_df, new_highs_list, CHARTS_DIR):
    
    # 出来高0の日は四本値が欠損しているため、スキップして可視化
    daily_stock_df = daily_stock_df.dropna(subset=["AdjC"])
    
    # 銘柄別にグループを形成
    groups = [
        (code, df.sort_values("Date"))
        for code, df in daily_stock_df.groupby("Code")
        if code in new_highs_list
    ]
    
    # 銘柄グループ別にチャートを作成
    Parallel(n_jobs=-1)(
        delayed(save_price_chart)(
            df,
            f"{CHARTS_DIR}/{code}.png"
        )
        for code, df in groups
    )