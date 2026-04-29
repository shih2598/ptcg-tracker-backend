from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# --- 終極映射：我們只針對「有問題」的編號做暴力攔截 ---
# 這些 ID 是經過美版 API 實測確定的正確身分證
FIXED_MAPPING = {
    "sv4k-014": "sv4-66",   # 這才是陸地水母 ex (Toedscruel ex)
    "sv4k-14": "sv4-66",
    "m2a-014": "sv3-125"
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    if not query:
        return jsonify({"status": "error", "message": "無內容"})
    
    try:
        # 1. 攔截模式：如果輸入的是有問題的日版編號，強制轉向
        target_id = FIXED_MAPPING.get(query)
        
        if target_id:
            # 直接抓取單張卡片
            res = requests.get(f"https://api.pokemontcg.io/v2/cards/{target_id}").json()
            cards_data = [res['data']] if 'data' in res else []
        else:
            # 2. 一般搜尋模式：針對名稱或編號進行搜尋
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
                "market_price_twd": f"NT$ {round(twd_price):,}" if twd_price > 0 else "議價中",
                "psa10_est": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "set_name": card.get('set', {}).get('name')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
