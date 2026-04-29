from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# 中文翻譯層 (這部分維持不變，確保中文能動)
TRANSLATE_MAP = {
    "炭小侍": "Charcadet", "噴火龍": "Charizard", "皮卡丘": "Pikachu"
}

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '').strip()
    if not query: return jsonify({"status": "error", "message": "無輸入"})

    search_term = TRANSLATE_MAP.get(query, query).lower()
    
    try:
        # --- 核心修正區：處理編號模式 ---
        if "-" in search_term:
            parts = search_term.split("-")
            prefix = parts[0]  # sv4k
            try:
                num = str(int(parts[1])) # 014 變成 14
                # 使用萬用字元 *：只要 ID 開頭是 sv4k 且編號是 14 就算中
                api_url = f"https://api.pokemontcg.io/v2/cards?q=number:\"{num}\" AND id:\"{prefix}*\""
            except:
                api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\""
        else:
            # 名稱搜尋模式
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\"&pageSize=12"

        res = requests.get(api_url).json()
        cards_data = res.get('data', [])

        results = []
        for card in cards_data:
            # 取得 TCGplayer 價格作為基底
            prices = card.get('tcgplayer', {}).get('prices', {})
            # 優先找 holofoil，沒有就找 normal
            p_data = prices.get('holofoil') or prices.get('normal') or prices.get('unlimitedHolofoil')
            market_price_usd = p_data.get('market', 0) if p_data else 0
            
            results.append({
                "card_name": query if query in TRANSLATE_MAP else card.get('name'),
                "id": card.get('id').upper(),
                "number": card.get('number'),
                "image_url_en": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(market_price_usd * 32.5):,}" if market_price_usd > 0 else "市場議價",
                "psa10": f"NT$ {round(market_price_usd * 32.5 * 4.5):,}" if market_price_usd > 0 else "---",
                # 加入模擬走勢 (這部分數值在正式銷售版可再對接歷史 API)
                "trend_7d": "+3.5%", 
                "trend_30d": "-1.2%"
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
