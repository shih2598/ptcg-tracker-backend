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
        return jsonify({"status": "error", "message": "請輸入搜尋編號"})
    
    try:
        # 針對 SV4K-014 這種格式進行拆解
        # 確保搜尋時精準鎖定 number (編號) 與 set.id (系列)
        if "-" in query:
            prefix, num = query.split("-")
            # 轉換為 API 接受的數字格式（去掉前導零）
            clean_num = str(int(num))
            api_url = f"https://api.pokemontcg.io/v2/cards?q=number:\"{clean_num}\" AND id:\"{prefix}*\""
        else:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}\"&pageSize=5"

        res = requests.get(api_url).json()
        cards_data = res.get('data', [])

        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            price_usd = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(price_usd) * 32.5
            
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
