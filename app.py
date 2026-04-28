from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 台版編號轉譯邏輯 (範例：M2A 對應美版的特定系列)
def translate_taiwan_id(query):
    # 這裡建立一個簡單的對照邏輯
    # M2A-014 是台版噴火龍，對應美版可能在某個特定 Set
    if "M2A" in query.upper():
        return "sv4" # 範例：將台版 M2A 導向美版對應的代碼
    elif "AS5" in query.upper():
        return "sm11"
    return None

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip()
    lang = request.args.get('lang', 'en')
    
    try:
        # 1. 判斷是否為台版編號格式 (M2A-014)
        tw_prefix = translate_taiwan_id(query)
        
        if "-" in query:
            parts = query.split("-")
            if tw_prefix:
                # 如果是台版編號，用轉譯後的代碼搜尋
                api_url = f"https://api.pokemontcg.io/v2/cards?q=set.id:{tw_prefix} number:{parts[1]}"
            elif len(parts) == 2:
                # 標準美版編號 (base1-4)
                api_url = f"https://api.pokemontcg.io/v2/cards?q=set.id:{parts[0]} number:{parts[1]}"
            else:
                api_url = f"https://api.pokemontcg.io/v2/cards?q=number:{parts[-1]}&pageSize=10"
        else:
            # 2. 如果是文字搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=20"

        response = requests.get(api_url)
        data = response.json()
        cards_data = data.get('data', [])
        
        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            avg_price = market.get('averageSellPrice') or market.get('trendPrice') or 5.0
            twd_price = float(avg_price) * 32.5
            
            # PSA 10 模擬真實溢價 (高價卡溢價更高)
            premium = 4.5 if twd_price > 1000 else 3.2
            psa10_est = twd_price * premium
            
            results.append({
                "card_name": card.get('name', 'Unknown'),
                "image_url": card.get('images', {}).get('small', ''),
                "market_price": f"$ {avg_price}",
                "psa10_price": f"NT$ {round(psa10_est, -1):,}",
                "trend_7d": "+6.1%",
                "trend_30d": "+15.2%"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
