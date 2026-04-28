from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 專業字典：將日版找不到的系列，自動映射到美版對應系列
# 這樣你搜尋 sv4k-014，它會自動幫你找 sv4-14 或對應的卡
SERIES_MAP = {
    "sv4k": "sv4",      # 古代咆哮 -> Paradox Rift
    "sv4m": "sv4",      # 未來閃光 -> Paradox Rift
    "sv5k": "sv5",      # 狂野軍力 -> Temporal Forces
    "sv8": "sv8",       # 超電突圍 -> Surging Sparks
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    
    try:
        cards_data = []
        # 第一階段：嘗試精準匹配（包含補零與不補零）
        if "-" in query:
            prefix, num = query.split("-")
            num_int = str(int(num))
            
            # 建立多重嘗試路徑
            attempts = [
                f"id:\"{query}\"",                 # 原始輸入
                f"id:\"{prefix}-{num_int}\"",      # 去零 ID
                f"(set.id:\"{prefix}\" AND number:\"{num_int}\")" # 系列+編號
            ]
            
            # 如果是日版系列，額外增加「美版對應路徑」
            if prefix in SERIES_MAP:
                us_prefix = SERIES_MAP[prefix]
                attempts.append(f"(set.id:\"{us_prefix}\" AND number:\"{num_int}\")")

            for q in attempts:
                api_url = f"https://api.pokemontcg.io/v2/cards?q={q}"
                res = requests.get(api_url).json().get('data', [])
                if res:
                    cards_data = res
                    break

        # 第二階段：備援模式（名稱搜尋）
        if not cards_data:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}\"&pageSize=10"
            cards_data = requests.get(api_url).json().get('data', [])

        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            avg_price = market.get('averageSellPrice') or market.get('trendPrice') or 15.0
            twd_price = float(avg_price) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id'),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(twd_price):,}",
                "psa10_price": f"NT$ {round(twd_price * 4.2, -1):,}",
                "set_info": f"{card.get('set', {}).get('name')} ({card.get('set', {}).get('id').upper()})"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
