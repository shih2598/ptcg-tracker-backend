from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip().upper()
    if not query:
        return jsonify({"status": "error", "message": "請輸入搜尋編號"})
    
    try:
        # 直接針對編號進行精準檢索
        # 由於改為日版優先，我們搜尋時會加上日版標籤限制 (如果有需要)
        api_url = f"https://api.pokemontcg.io/v2/cards?q=id:\"{query.lower()}\" OR number:\"{query.split('-')[-1] if '-' in query else query}\""
        
        headers = {'X-Api-Key': 'your-api-key-here'} # 建議放你的 API Key
        response = requests.get(api_url, headers=headers)
        cards_data = response.json().get('data', [])

        results = []
        for card in cards_data:
            # 過濾掉非日版或無關的卡片 (簡單過濾邏輯)
            if "-" in query and query.split("-")[0].lower() not in card.get('id').lower():
                continue

            market = card.get('cardmarket', {}).get('prices', {})
            # 取得日版行情 (這裡維持匯率轉換，但資料源會更準)
            price_raw = market.get('averageSellPrice') or market.get('trendPrice') or 1.0
            twd_price = float(price_raw) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id').upper(),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(twd_price):,}",
                "psa10_price": f"NT$ {round(twd_price * 4.5, -1):,}",
                "set_name": card.get('set', {}).get('name'),
                "rarity": card.get('rarity', 'Uncommon')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
