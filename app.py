from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# --- 核心對照表：這就是殺掉 Zekrom 的關鍵 ---
# 邏輯：只要輸入日版編號，我們就強行指定美版正確 ID
DATA_BRIDGE = {
    "sv4k-014": "sv4-66",   # 陸地水母 ex (日版 14 號 -> 美版 66 號)
    "sv4k-14": "sv4-66",
    "m2a-014": "sv3-125",
    "sv8-106": "sv8-106"
}

# --- 系列映射 ---
SET_MAP = {
    "sv4k": "Paradox Rift",
    "sv8": "Surging Sparks"
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    if not query:
        return jsonify({"status": "error", "message": "無輸入內容"})
    
    try:
        cards_data = []
        
        # 邏輯 1：優先走我們設定的精準對照 (Mapping)
        if query in DATA_BRIDGE:
            target_id = DATA_BRIDGE[query]
            res = requests.get(f"https://api.pokemontcg.io/v2/cards/{target_id}").json()
            if 'data' in res:
                cards_data = [res['data']]

        # 邏輯 2：如果沒中對照表，嘗試「系列+編號」精準匹配
        if not cards_data and "-" in query:
            prefix, num = query.split("-")
            if prefix in SET_MAP:
                s_name = SET_MAP[prefix]
                api_url = f"https://api.pokemontcg.io/v2/cards?q=set.name:\"{s_name}\" number:\"{int(num)}\""
                cards_data = requests.get(api_url).json().get('data', [])

        # 邏輯 3：以上皆失敗，才用名稱搜尋 (這時才有可能出現 Zekrom，作為墊底)
        if not cards_data:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}\"&pageSize=5"
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
                "market_price_twd": f"NT$ {round(twd_price):,}" if twd_price > 0 else "計算中",
                "psa10_est": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "set_name": card.get('set', {}).get('name')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
