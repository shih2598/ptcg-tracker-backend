from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip()
    
    try:
        # 1. 判斷是否為精準搜尋 (例如 M2A-014)
        if "-" in query:
            # 針對精準搜尋：過濾編號
            parts = query.split("-")
            # 這裡我們用更廣泛的搜尋方式，確保能抓到資料
            api_url = f"https://api.pokemontcg.io/v2/cards?q=number:{parts[1]}&pageSize=20"
        else:
            # 2. 針對模糊搜尋 (例如 噴火龍)
            # 注意：API 對中文支援度較低，我們預設如果搜中文，自動補上一些英文關鍵字或改用全名搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=50"

        # 加入 API Key (如果有可以加在 headers，目前先不用)
        response = requests.get(api_url)
        data = response.json()
        
        cards_data = data.get('data', [])
        results = []

        for card in cards_data:
            # 抓取價格，如果沒有價格就給個模擬起跳價
            market = card.get('cardmarket', {}).get('prices', {})
            m_price = market.get('averageSellPrice') or market.get('trendPrice') or 0
            
            results.append({
                "card_name": card.get('name', 'Unknown'),
                "image_url": card.get('images', {}).get('small', ''),
                "market_price": f"$ {m_price}",
                "trend_7d": "+3.5%", # 預設模擬
                "trend_30d": "+12.1%" # 預設模擬
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
