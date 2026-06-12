import os
import sys
from flask import Flask, request, jsonify, render_template

# Vercel isolates the /api folder. We must force the system path up one 
# directory level so it can access vaporpic.py and config.ini in the root.
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from vaporpic import VidnodeApi

# Explicitly map the templates directory for the Flask rendering engine
template_dir = os.path.join(root_dir, 'templates')
app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    data = request.json
    media_type = data.get('media_type', 'movie')
    title = data.get('title', '').strip()
    season = data.get('season', '').strip()
    episode = data.get('episode', '').strip()

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    try:
        if media_type == 'tvod':
            va = VidnodeApi(media_type, title, s=season, e=episode)
        else:
            va = VidnodeApi(media_type, title)

        search_url = va.assemble_search_url()
        if not search_url:
            return jsonify({'error': 'Title not found on the source.'}), 404

        media_url = va.assemble_media_url(search_url)

        # The bot_mode=True parameter is structurally critical here. 
        # It circumvents the IP-mismatch by extracting the browser-safe web player 
        # link instead of the raw .mp4 hotlink which would trigger a 403 Forbidden.
        link_dict = va.scrape_final_links(media_url, bot_mode=True)

        return jsonify({'success': True, 'data': link_dict})

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
