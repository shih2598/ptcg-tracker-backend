from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 內建翻譯字典：支援中文搜尋 (你可以隨時手動增加常用熱門卡)
TRANSLATE_MAP = {
    "炭小侍": "Charcadet",
    "噴火龍": "Charizard",
    "皮卡丘": "Pikachu",
    "密勒頓": "Miraidon",
    "古勒頓": "Koraidon"
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    user_query = request.args.get('name', '').strip()
    if not user_query:
        return jsonify({"status": "error", "message": "無輸入"})

    # 1. 優先判斷是否為中文搜尋
    search_term = TRANSLATE_MAP.get(user_query, user_query).lower()

    try:
        # 2. 判斷是否為日版編號格式 (如 SV4K-014)
        if "-" in search_term:
            parts = search_term.split("-")
            prefix = parts[0]
            try:
                # 自動修正編號：014 -> 14 (API 認得的格式)
                num = str(int(parts[1]))
                api_url = f"https://api.pokemontcg.io/v2/cards?q=id:\"{prefix}-{num}\" OR (number:\"{num}\" AND id:\"{prefix}*\")"
            except:
                api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\""
        else:
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\"&pageSize=10"

        res = requests.get(api_url).json()
        cards_data = res.get('data', [])

        results = []
        for card in cards_data:
            # 取得行情與匯率換算
            market = card.get('cardmarket', {}).get('prices', {})
            price_raw = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(price_raw) * 32.5
            
            results.append({
                "card_name": user_query if user_query in TRANSLATE_MAP else card.get('name'),
                "id": card.get('id').upper(),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(twd_price):,}" if twd_price > 0 else "市場議價",
                "psa10": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "set_name": card.get('set', {}).get('name')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
