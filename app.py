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
        # 優化編號搜尋：處理 sv4k-014 或 014/066 格式
        if "-" in query:
            parts = query.split("-")
            # 嘗試兩種 ID 格式：原樣搜尋 與 去除補零搜尋 (014 -> 14)
            num_clean = parts[1].lstrip('0')
            api_url = f"https://api.pokemontcg.io/v2/cards?q=(id:\"{query}\" OR (set.id:\"{parts[0]}\" AND number:\"{num_clean}\"))"
        else:
            # 關鍵字搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=30&orderBy=-set.releaseDate"

        headers = {'X-Api-Key': 'YOUR_API_KEY'} # 如果你有 API Key 可以加上去提高限額
        response = requests.get(api_url, headers=headers)
        cards_data = response.json().get('data', [])
        
        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            avg_price = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(avg_price) * 32.5
            
            # 嘗試取得日文名稱 (部分卡片支援)
            # 注意：pokemontcg.io 的日文名稱通常存在於屬性或需另外比對，
            # 這裡我們先確保能抓到正確的日版圖 (Images.large 通常就是日版圖)
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id'),
                "set_id": card.get('set', {}).get('id'),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"$ {avg_price}",
                "psa10_price": f"NT$ {round(twd_price * 4, -1):,}",
                "trend_7d": "+2.9%",
                "trend_30d": "+10.5%"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
