from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    if not query:
        return jsonify({"status": "error", "message": "無輸入"})
    
    try:
        # 核心邏輯：處理 sv4k-014 -> sv4k-14
        if "-" in query:
            parts = query.split("-")
            prefix = parts[0]
            # 強制將編號轉為整數再轉回字串，去除前導 0
            num = str(int(parts[1]))
            target_id = f"{prefix}-{num}"
            # 使用 id 精準搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=id:\"{target_id}\""
        else:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}\"&pageSize=5"

        res = requests.get(api_url).json()
        cards_data = res.get('data', [])

        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            # 取得日版行情 (換算台幣)
            price_raw = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(price_raw) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id').upper(),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(twd_price):,}" if twd_price > 0 else "市場議價",
                "psa10": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "rarity": card.get('rarity', '一般版本')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
