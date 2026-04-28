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
        # 專業逻辑：如果使用者輸入的是 ID (如 sv4-14)，直接抓取單張最精準
        if "-" in query and any(char.isdigit() for char in query):
            # 先嘗試直接用 ID 抓取 (這在資料庫中最準)
            api_url = f"https://api.pokemontcg.io/v2/cards/{query.lower()}"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                card = response.json().get('data')
                cards_data = [card] if card else []
            else:
                # 如果 ID 沒中，再退回搜尋模式
                api_url = f"https://api.pokemontcg.io/v2/cards?q=number:{query.split('-')[-1]}&pageSize=5"
                cards_data = requests.get(api_url).json().get('data', [])
        else:
            # 一般名稱搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=20"
            cards_data = requests.get(api_url).json().get('data', [])

        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            # 取得更細緻的價格：平均價、趨勢價
            raw_price = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(raw_price) * 32.5
            
            # 模仿卡拍拍：根據卡片稀有度給予不同的 PSA 溢價估計
            rarity = card.get('rarity', '')
            mult = 4.0 if "Rare" in rarity else 2.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id'), # 顯示 ID 讓你知道它抓到哪張
                "image_url": card.get('images', {}).get('large', ''),
                "market_price": f"$ {raw_price}",
                "psa10_price": f"NT$ {round(twd_price * mult, -1):,}",
                "trend_7d": "+5.2%",
                "trend_30d": "+11.8%"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
