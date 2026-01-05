from flask import Flask, jsonify
import os
import praw
import re
import pandas as pd
from datetime import datetime

reddit = praw.Reddit(
    client_id="26oxZPe1Jd05btZUJiEFqA",
    client_secret="K2yj5uNh1dJDryrormSGOSUejLZzoA",
    user_agent="AnalyseurVenteIntelligente v2.0"
)
def extract_price(text):
    """
    Tente d'extraire un prix (ex: $50, 50€, 50 USD) du texte via une expression régulière simple.
    """
    # Regex basique pour les devises courantes ($, €, Ar, etc.)
    price_pattern = r'(\$|€|Ar)\s?(\d+(?:[.,]\d{1,2})?)'
    match = re.search(price_pattern, text)
    if match:
        return match.group(0)
    return None

def scrape_reddit_products(keywords, subreddits="all", limit=50):
    """
    Recherche des produits sur Reddit basés sur des mots-clés.
    """
    print(f"--- Recherche de '{keywords}' dans r/{subreddits} ---")
    
    products_data = []
    
    # Recherche dans le subreddit spécifié (ou "all")
    subreddit = reddit.subreddit(subreddits)
    
    # On cherche les nouveaux posts correspondants à la requête
    for submission in subreddit.search(keywords, sort='hot', limit=limit):
        
        # Combiner le titre et le contenu pour l'analyse
        full_text = f"{submission.title} {submission.selftext}"
        
        # Tentative d'extraction de prix
        price = extract_price(full_text)
        
        product_info = {
            'titre': submission.title,
            'prix_estime': price, # Peut être None si pas trouvé
            'url': submission.url,
            'date_creation': datetime.fromtimestamp(submission.created_utc),
            'subreddit': submission.subreddit.display_name,
            'score': submission.score,
            'nombre_commentaires': submission.num_comments,
            'description': submission.selftext[:200] + "..." # Aperçu de la description
            
        }
        
        products_data.append(product_info)
    
    return pd.DataFrame(products_data)

# --- EXEMPLE D'UTILISATION ---

# Mots-clés pour trouver des produits (à adapter selon votre niche)
# Ex: "selling laptop", "à vendre téléphone", etc.
app = Flask(__name__)
@app.route('/')
def home():
    search_query = "selling laptop" 

    # Subreddits ciblés (ex: hardwareswap, leboncoin, ou "all" pour tout reddit)
    target_subreddits = "hardwareswap+appleswap" 

    df_produits = scrape_reddit_products(search_query, target_subreddits, limit=50)

    # Affichage des résultats
    if not df_produits.empty:
        return jsonify(df_produits.to_json(orient='records'))
    else:
        print("Aucun produit trouvé.")


@app.route('/status')
def status():
    return jsonify({"status": "ok"})
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)