from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip()
    if not query: return jsonify({"status": "error", "message": "無輸入"})

    try:
        # 1. 處理編號格式 (sv4k-014 -> id: "sv4k-14")
        if "-" in query:
            parts = query.split("-")
            prefix = parts[0].lower()
            try:
                num = str(int(parts[1]))
                # 寬鬆搜尋：抓 ID 包含 prefix 且編號為 num 的卡
                api_url = f"https://api.pokemontcg.io/v2/cards?q=number:\"{num}\" AND id:\"{prefix}*\""
            except:
                api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}*\""
        else:
            # 2. 全圖鑑名稱搜尋 (支援英文名，如 Pikachu, Charizard)
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}*\"&pageSize=20"

        res = requests.get(api_url).json()
        cards_data = res.get('data', [])

        results = []
        for card in cards_data:
            # 取得 TCGplayer 市場價格
            prices = card.get('tcgplayer', {}).get('prices', {})
            p_data = prices.get('holofoil') or prices.get('normal') or prices.get('unlimitedHolofoil')
            market_usd = p_data.get('market', 0) if p_data else 0
            
            results.append({
                "id": card.get('id'), # 例如 sv4k-14
                "number": card.get('number'), # 例如 14
                "en_name": card.get('name'),
                "image_en": card.get('images', {}).get('large'),
                "twd_price": round(market_usd * 32.5),
                "psa10_ref": round(market_usd * 32.5 * 4.5, -1)
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8765)))
