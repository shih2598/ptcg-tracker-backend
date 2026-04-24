import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_market_analysis(card_name):
    # 支援中文搜尋
    translate_dict = {"噴火龍": "Charizard", "皮卡丘": "Pikachu", "超夢": "Mewtwo", "洛奇亞": "Lugia"}
    search_term = translate_dict.get(card_name, card_name)
    
    # 抓取 TCGPlayer 資料
    api_url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\"&pageSize=8"
    
    try:
        response = requests.get(api_url, timeout=10)
        res_json = response.json()
        cards_list = []
        for card in res_json.get('data', []):
            prices = card.get('tcgplayer', {}).get('prices', {})
            market_val = prices.get('holofoil', {}).get('market') or prices.get('normal', {}).get('market') or 0
            
            cards_list.append({
                "card_name": card.get('name'),
                "set_info": card.get('set').get('name'),
                "image_url": card.get('images').get('small'),
                "market_price": f"$ {market_val}",
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
        return cards_list
    except:
        return []

@app.route('/api/search', methods=['GET'])
def search():
    name = request.args.get('name')
    results = get_market_analysis(name)
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    # 這裡很關鍵：雲端會自動分配 Port，不能寫死 8765
    port = int(os.environ.get('PORT', 8765))
    app.run(host='0.0.0.0', port=port)