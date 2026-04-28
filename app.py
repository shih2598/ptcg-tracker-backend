from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/search', methods=['GET'])
def search_cards():
    query = request.args.get('name', '')
    
    try:
        # 1. 處理精準搜尋邏輯 (針對 M2A-014 這種格式)
        if "-" in query:
            # 拆解出系列或編號進行精準匹配
            parts = query.split("-")
            # 使用 pokemontcg.io 的語法，精準對接編號
            api_url = f"https://api.pokemontcg.io/v2/cards?q=number:{parts[1]}&pageSize=30"
        else:
            # 2. 處理大方向搜尋，將數量調高至 50 筆，滿足大範圍瀏覽
            api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}*&pageSize=50"

        response = requests.get(api_url)
        data = response.json()
        
        results = []
        for card in data.get('data', []):
            # 取得市場價格，若無則設為 0
            m_price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0)
            
            # 這裡我們先用模擬算法生成 30D 漲幅，等下一階段對接資料庫歷史數據
            # 這樣介面就能先跑出你想要的紅綠字效果
            results.append({
                "card_name": card.get('name'),
                "image_url": card.get('images', {}).get('small'),
                "market_price": f"$ {m_price}",
                "set_info": f"{card.get('set', {}).get('name')} {card.get('number')}",
                "update_time": "2026-04-28",
                "trend_7d": "+5.2%",  # 模擬 7天漲幅
                "trend_30d": "+18.5%" # 模擬 30天漲幅 (新增需求)
            })
            
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8765))
    app.run(host='0.0.0.0', port=port)
