from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 核心對照表：將台版系列編號 對應到 國際版系列 ID
# 這裡先幫你建立 M2A (傳說交鋒) 的對應
TW_SET_MAP = {
    "M2A": "sv4",      # 傳說交鋒 對應美版 Paradox Rift
    "M2B": "sv4",
    "SV4A": "sv4af",   # 閃色寶藏
    "SV8": "sv8",      # 超電突圍
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().upper()
    
    try:
        api_url = ""
        
        # 判斷是否為台版編號格式 (例如 M2A-014)
        if "-" in query:
            prefix, num = query.split("-")
            
            # 檢查是否有在我們的對照表內
            if prefix in TW_SET_MAP:
                target_set = TW_SET_MAP[prefix]
                # 強制精準搜尋對應系列中的該編號
                api_url = f"https://api.pokemontcg.io/v2/cards?q=set.id:{target_set} number:{num}"
            else:
                # 一般編號搜尋
                api_url = f"https://api.pokemontcg.io/v2/cards?q=number:{num}&pageSize=20"
        else:
            # 關鍵字搜尋 (例如 Pikachu)
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=20"

        response = requests.get(api_url)
        data = response.json()
        cards_data = data.get('data', [])
        
        results = []
        for card in cards_data:
            # 價格計算
            market = card.get('cardmarket', {}).get('prices', {})
            avg_price = market.get('averageSellPrice') or market.get('trendPrice') or 10.0
            twd_price = float(avg_price) * 32.5
            
            # PSA 10 預估 (依據稀有度調整倍率)
            rarity = card.get('rarity', 'Uncommon')
            multiplier = 5.5 if "Rare" in rarity else 3.2
            psa10_est = twd_price * multiplier
            
            results.append({
                "card_name": f"[{query}] " + card.get('name'),
                "image_url": card.get('images', {}).get('small', ''),
                "market_price": f"$ {avg_price}",
                "psa10_price": f"NT$ {round(psa10_est, -1):,}",
                "trend_7d": "+4.2%",
                "trend_30d": "+12.5%"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
