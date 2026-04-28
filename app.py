from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().lower()
    
    try:
        cards_data = []
        # 1. 處理編號格式 (例如 sv4k-014)
        if "-" in query:
            prefix, num = query.split("-")
            num_int = str(int(num)) # 14
            num_pad = num.zfill(3) # 014
            
            # 同時嘗試三種組合，提高日版命中率
            search_queries = [
                f"id:\"{prefix}-{num_int}\"",
                f"id:\"{prefix}-{num_pad}\"",
                f"(set.id:\"{prefix}\" AND number:\"{num_int}\")"
            ]
            
            for q in search_queries:
                api_url = f"https://api.pokemontcg.io/v2/cards?q={q}"
                res = requests.get(api_url).json().get('data', [])
                if res:
                    cards_data = res
                    break
        
        # 2. 如果編號沒結果，或者不是編號格式，用名稱搜
        if not cards_data:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=20&orderBy=-set.releaseDate"
            cards_data = requests.get(api_url).json().get('data', [])

        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            avg_price = market.get('averageSellPrice') or market.get('trendPrice') or 0
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id'),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"$ {avg_price}",
                "psa10_price": f"NT$ {round(float(avg_price) * 32.5 * 4.5, -1):,}",
                "set_name": card.get('set', {}).get('name')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
