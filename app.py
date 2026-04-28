from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# --- 專業資料對照橋樑 (精準度核心) ---
# 邏輯：[日/台版編號] -> [美版 API 實際 ID]
DATA_BRIDGE = {
    "sv4k-014": "sv4-66",    # 陸地水母 ex (日版 sv4k-014 -> 美版 sv4-66)
    "sv4k-14": "sv4-66",
    "m2a-014": "sv3-125",   # 範例：噴火龍 ex
    "sv8-106": "sv8-106",   # 超電突圍 (若編號恰巧相同)
}

# --- 系列名稱對照 ---
SET_MAP = {
    "sv4k": "Paradox Rift",
    "sv4m": "Paradox Rift",
    "sv8": "Surging Sparks",
    "sv7": "Stellar Crown"
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    
    try:
        cards_data = []
        
        # 1. 第一層：精準 ID 橋接
        if query in DATA_BRIDGE:
            target_id = DATA_BRIDGE[query]
            api_url = f"https://api.pokemontcg.io/v2/cards/{target_id}"
            res = requests.get(api_url).json()
            if 'data' in res:
                cards_data = [res['data']]

        # 2. 第二層：系列映射搜尋
        if not cards_data and "-" in query:
            prefix, num = query.split("-")
            num_int = str(int(num))
            
            if prefix in SET_MAP:
                set_name = SET_MAP[prefix]
                # 嘗試在美版對應系列中搜尋該編號 (雖然不一定 100% 中，但比亂搜好)
                api_url = f"https://api.pokemontcg.io/v2/cards?q=set.name:\"{set_name}\" number:\"{num_int}\""
                cards_data = requests.get(api_url).json().get('data', [])

        # 3. 第三層：通用搜尋
        if not cards_data:
            # 優先搜尋 ID
            api_url = f"https://api.pokemontcg.io/v2/cards?q=id:\"{query}\" OR name:\"{query}\"&pageSize=12"
            cards_data = requests.get(api_url).json().get('data', [])

        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            # 取得即時行情並轉換台幣 (匯率 32.5)
            price_usd = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(price_usd) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id').toUpperCase(),
                "image_url": card.get('images', {}).get('large'),
                "market_price_twd": f"NT$ {round(twd_price):,}",
                "psa10_est": f"NT$ {round(twd_price * 4.5, -1):,}",
                "set_name": card.get('set', {}).get('name')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
