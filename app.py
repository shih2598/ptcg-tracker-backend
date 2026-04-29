from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip()
    if not query:
        return jsonify({"status": "error", "message": "請輸入內容"})
    
    try:
        # 1. 判定搜尋模式
        if "-" in query:
            # 編號模式 (例如: sv4k-014)
            parts = query.split("-")
            prefix = parts[0].lower()
            try:
                num = str(int(parts[1])) # 014 -> 14
                # 同時搜尋 ID 精準匹配 或 系列+編號 組合
                api_url = f"https://api.pokemontcg.io/v2/cards?q=(id:\"{prefix}-{num}\") OR (number:\"{num}\" AND id:\"{prefix}*\")"
            except:
                api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}\""
        else:
            # 名稱模式 (例如: 炭小侍 或 Charcadet)
            # 因為 API 主要是英文，我們支援名稱模糊搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}*\"&pageSize=10"

        res = requests.get(api_url).json()
        cards_data = res.get('data', [])

        # 2. 資料整理
        results = []
        for card in cards_data:
            market = card.get('cardmarket', {}).get('prices', {})
            price_raw = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(price_raw) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id').upper(),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(twd_price):,}" if twd_price > 0 else "市場議價",
                "psa10": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "set_name": card.get('set', {}).get('name'),
                "rarity": card.get('rarity', '一般版本')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
