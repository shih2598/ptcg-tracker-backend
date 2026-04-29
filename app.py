from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    user_input = request.args.get('name', '').strip().lower()
    if not user_input:
        return jsonify({"status": "error", "message": "請輸入內容"})
    
    try:
        # 1. 處理輸入格式：將 sv4k-014 轉換為 sv4k-14
        if "-" in user_input:
            parts = user_input.split("-")
            prefix = parts[0]
            # 將 014 轉為數字 14 再轉回字串，去除前導零
            num = str(int(parts[1]))
            # 這是美版 API 收錄日版卡片的標準 ID 格式
            target_id = f"{prefix}-{num}"
            api_url = f"https://api.pokemontcg.io/v2/cards?q=id:\"{target_id}\""
        else:
            # 一般關鍵字搜尋
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{user_input}\"&pageSize=5"

        headers = {'X-Api-Key': 'YOUR_API_KEY'} # 若有 Key 可加快速度
        response = requests.get(api_url, headers=headers)
        cards_data = response.json().get('data', [])

        results = []
        for card in cards_data:
            # 取得日版環境行情
            market = card.get('cardmarket', {}).get('prices', {})
            # 優先使用平均售價
            usd_price = market.get('averageSellPrice') or market.get('trendPrice') or 0
            twd_price = float(usd_price) * 32.5
            
            results.append({
                "card_name": card.get('name'),
                "id": card.get('id').upper(),
                "image_url": card.get('images', {}).get('large'),
                "market_price": f"NT$ {round(twd_price):,}" if twd_price > 0 else "市場議價",
                "psa10": f"NT$ {round(twd_price * 4.5, -1):,}" if twd_price > 0 else "---",
                "rarity": card.get('rarity', '一般版本'),
                "set_name": card.get('set', {}).get('name')
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
