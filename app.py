from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# --- 終極精準對照表 (使用美版 API 唯一 ID) ---
DATA_BRIDGE = {
    # 日版 sv4k-014 真正的美版身分證是 sv4-201 (Toedscruel ex)
    "sv4k-014": "sv4-201", 
    "sv4k-14": "sv4-201",
    # 日版 sm12a-147 (通常是全圖莉莉艾或熱門卡) 需對應美版 ID
    "sm12a-147": "sm12-251" 
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    if not query: return jsonify({"status": "error", "message": "無輸入"})
    
    try:
        cards_data = []
        # 邏輯 1：身分證直接鎖定 (最準)
        if query in DATA_BRIDGE:
            target_id = DATA_BRIDGE[query]
            res = requests.get(f"https://api.pokemontcg.io/v2/cards/{target_id}").json()
            if 'data' in res: cards_data = [res['data']]

        # 邏輯 2：若沒在表內，才走關鍵字搜尋
        if not cards_data:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}\" OR id:\"{query}\"&pageSize=4"
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
                "market_price_twd": f"NT$ {round(twd_price):,}" if twd_price > 0 else "議價",
                "psa10_est": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "set_name": card.get('set', {}).get('name')
            })
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
