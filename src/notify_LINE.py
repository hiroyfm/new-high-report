import requests

def create_message(new_highs_df, newest_market_date, report_url):
    ### 加工したデータから送信するテキストを作成

    # 新高値更新銘柄数を市場別に集計
    all_len = len(new_highs_df)
    prime_len = len(new_highs_df[new_highs_df["MktNm"] == "プライム"])
    standard_len = len(new_highs_df[new_highs_df["MktNm"] == "スタンダード"])
    growth_len = len(new_highs_df[new_highs_df["MktNm"] == "グロース"])

    # LINEのメッセージ文をリストで作成
    lines = []

    lines.append(f"{newest_market_date}の新高値更新銘柄レポートをお届けします。")
    lines.append("")
    lines.append(f"【プライム市場】 {prime_len}銘柄")
    lines.append(f"【スタンダード市場】 {standard_len}銘柄")
    lines.append(f"【グロース市場】 {growth_len}銘柄")
    lines.append("")
    lines.append(f"【3市場合計】 {all_len}銘柄")

    lines.append("")
    lines.append("Let's テンバガー！")

    lines.append("")
    
    # レポートのURLを添付
    lines.append(f"{report_url}")
    
    # メッセージリストを文字列に変換
    message = "\n".join(lines)
    
    return message

def send_message(message, LINE_CHANNEL_ACCESS_TOKEN, line_base_url, Path_broadcast):
    ### LINEに通知
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messages": [
            {
                "type": "text",
                "text": message
            }        
        ]
    }

    res = requests.post(line_base_url + Path_broadcast, headers=headers, json=payload)

    print(res.status_code)
    print(res.text)

    res.raise_for_status()


def send_report_to_LINE(
    new_highs_df, 
    newest_market_date, 
    report_url, 
    LINE_CHANNEL_ACCESS_TOKEN, 
    line_base_url, 
    Path_broadcast
):
    ### LINEにレポートを送信
    
    # 送信メッセージを作成
    message = create_message(new_highs_df, newest_market_date, report_url)
    
    # LINEに送信
    send_message(message, LINE_CHANNEL_ACCESS_TOKEN, line_base_url, Path_broadcast)