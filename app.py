from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip()
    # 接收前端傳來的語言設定，預設為英文 (en)
    lang = request.args.get('lang', 'en')
    
    try:
        # 構建 API 搜尋網址
        # 如果包含橫槓 (如 M2A-014)，嘗試精準搜尋編號
        if "-" in query:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=number:{query.split('-')[-1]}&pageSize=10"
        else:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=20"

        response = requests.get(api_url)
        data = response.json()
        cards_data = data.get('data', [])
        
        results = []
        for card in cards_data:
            # 取得市場平均價 (USD)
            market_prices = card.get('cardmarket', {}).get('prices', {})
            avg_price = market_prices.get('averageSellPrice') or market_prices.get('trendPrice') or 5.0
            
            # 轉換成台幣
            twd_price = float(avg_price) * 32.5
            
            # PSA 10 估算邏輯：通常是裸卡價的 2.5 到 4 倍
            psa10_est = twd_price * 3.2
            
            results.append({
                "card_name": card.get('name', 'Unknown'),
                "image_url": card.get('images', {}).get('small', ''),
                "market_price": f"$ {avg_price}",
                "psa10_price": f"NT$ {round(psa10_est, -1):,}", # 格式化為台幣並千分位
                "trend_7d": "+2.4%",
                "trend_30d": "+8.7%"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
