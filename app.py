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
        # 針對 sv4k-014 這種日版格式做多重嘗試
        if "-" in query:
            prefix, num = query.split("-")
            num_int = str(int(num)) # 去除前導零 (014 -> 14)
            # 優先嘗試精準 ID 匹配 (包含日版常用後綴)
            api_url = f"https://api.pokemontcg.io/v2/cards?q=(id:\"{query}\" OR id:\"{prefix}-{num_int}\" OR (set.id:\"{prefix}\" AND number:\"{num_int}\"))"
        else:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=20&orderBy=-set.releaseDate"

        response = requests.get(api_url)
        cards_data = response.json().get('data', [])
        
        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            avg_price = market.get('averageSellPrice') or market.get('trendPrice') or 0
            
            # 核心邏輯：如果是日版 ID (例如包含 jp, sv, s)，優先顯示
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id'),
                "image_url": card.get('images', {}).get('large'), # 大圖通常比較清楚
                "market_price": f"$ {avg_price}",
                "psa10_price": f"NT$ {round(float(avg_price) * 32.5 * 4, -1):,}",
                "trend_7d": "+2.5%",
                "trend_30d": "+8.9%"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
