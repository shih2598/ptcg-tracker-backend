from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# --- 中文名稱映射表 (銷售常用熱門卡) ---
# 這是為了解決 API 聽不懂中文的問題，我們可以手動擴充
CN_TO_EN = {
    "炭小侍": "Charcadet",
    "噴火龍": "Charizard",
    "皮卡丘": "Pikachu",
    "陸地水母": "Toedscruel",
    "捷克羅姆": "Zekrom"
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip()
    if not query: return jsonify({"status": "error", "message": "無輸入"})
    
    # 轉換中文到英文搜尋
    search_term = CN_TO_EN.get(query, query).lower()
    
    try:
        # 1. 處理編號格式 (例如 SV4K-014 -> sv4k-14)
        if "-" in search_term:
            parts = search_term.split("-")
            prefix = parts[0]
            try:
                num = str(int(parts[1])) # 014 轉 14
                api_url = f"https://api.pokemontcg.io/v2/cards?q=id:\"{prefix}-{num}\" OR (number:\"{num}\" AND id:\"{prefix}*\")"
            except:
                api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\""
        else:
            # 2. 處理名稱搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\"&pageSize=12"

        res = requests.get(api_url).json()
        cards_data = res.get('data', [])

        results = []
        for card in cards_data:
            # 這裡我們只抓日版卡片 (如果 ID 包含關鍵字)
            # 或者不篩選，直接顯示找到的結果
            market = card.get('cardmarket', {}).get('prices', {})
            price_usd = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(price_usd) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id').upper(),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(twd_price):,}" if twd_price > 0 else "市場議價",
                "psa10": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---"
            })
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
