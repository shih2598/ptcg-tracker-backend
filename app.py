from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
# 強化 CORS 設定，確保 GitHub Pages 能順利讀取
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- 專業資料對照橋樑 ---
# 確保 sv4k-014 一定能對應到美版的 Paradox Rift (sv4) 第 66 號
DATA_BRIDGE = {
    "sv4k-014": "sv4-66",
    "sv4k-14": "sv4-66",
    "sv8-106": "sv8-106",
    "m2a-014": "sv3-125"
}

# 系列對照
SET_MAP = {
    "sv4k": "Paradox Rift",
    "sv4m": "Paradox Rift",
    "sv8": "Surging Sparks"
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    if not query:
        return jsonify({"status": "error", "message": "No query provided"})
    
    try:
        cards_data = []
        
        # 邏輯 1：優先查對照表
        if query in DATA_BRIDGE:
            target_id = DATA_BRIDGE[query]
            res = requests.get(f"https://api.pokemontcg.io/v2/cards/{target_id}").json()
            if 'data' in res:
                cards_data = [res['data']]

        # 邏輯 2：查系列與編號
        if not cards_data and "-" in query:
            prefix, num = query.split("-")
            num_int = str(int(num))
            if prefix in SET_MAP:
                s_name = SET_MAP[prefix]
                api_url = f"https://api.pokemontcg.io/v2/cards?q=set.name:\"{s_name}\" number:\"{num_int}\""
                cards_data = requests.get(api_url).json().get('data', [])

        # 邏輯 3：通用兜底搜尋
        if not cards_data:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=id:\"{query}\" OR name:\"{query}\"&pageSize=8"
            cards_data = requests.get(api_url).json().get('data', [])

        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            price_usd = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(price_usd) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id').upper(),
                "image_url": card.get('images', {}).get('large'),
                "market_price_twd": f"NT$ {round(twd_price):,}" if twd_price > 0 else "計算中...",
                "psa10_est": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "set_name": card.get('set', {}).get('name')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
