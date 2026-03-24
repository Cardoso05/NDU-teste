from flask import Flask, jsonify, request
from flask_cors import CORS
from flasgger import Swagger
from service import MyService
from exception import *
import pandas as pd
import json
import os

app = Flask(__name__)
CORS(app)
swagger = Swagger(app)

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NDU - API de Torneios</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;flex-direction:column;align-items:center}
.hero{text-align:center;padding:60px 20px 40px}
.hero h1{font-size:2.8rem;font-weight:800;background:linear-gradient(135deg,#38bdf8,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.hero p{font-size:1.1rem;color:#94a3b8;max-width:500px;margin:0 auto}
.badge{display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:20px;padding:6px 16px;font-size:.8rem;color:#38bdf8;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;max-width:900px;width:100%;padding:0 20px;margin-bottom:40px}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;transition:all .2s}
.card:hover{border-color:#38bdf8;transform:translateY(-2px);box-shadow:0 8px 30px rgba(56,189,248,.1)}
.card h3{font-size:1rem;color:#f1f5f9;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.card .icon{font-size:1.3rem}
.card p{font-size:.85rem;color:#64748b;margin-bottom:12px}
.card code{display:block;background:#0f172a;border-radius:8px;padding:10px 14px;font-size:.8rem;color:#38bdf8;word-break:break-all;font-family:'SF Mono',Monaco,Consolas,monospace}
.footer{padding:30px;text-align:center;color:#475569;font-size:.8rem}
.footer a{color:#38bdf8;text-decoration:none}
.status{display:flex;align-items:center;gap:8px;justify-content:center;margin-top:16px}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
</style>
</head>
<body>
<div class="hero">
<div class="badge">v1.0</div>
<h1>NDU API</h1>
<p>API de dados do torneio universitario de futsal NDU</p>
<div class="status"><span class="dot"></span><span style="font-size:.85rem;color:#22c55e">Online</span></div>
</div>
<div class="grid">
<div class="card">
<h3><span class="icon">&#9917;</span> Modalidades</h3>
<p>Lista todas as modalidades e series disponiveis</p>
<code>GET /api/modalities</code>
</div>
<div class="card">
<h3><span class="icon">&#127942;</span> Jogos</h3>
<p>Jogos por modalidade e serie (ex: FM serie A)</p>
<code>GET /api/games/FM/A</code>
</div>
<div class="card">
<h3><span class="icon">&#128200;</span> Ranking</h3>
<p>Classificacao dos grupos por modalidade</p>
<code>GET /api/ranking/FM/A</code>
</div>
<div class="card">
<h3><span class="icon">&#9878;</span> Confrontos</h3>
<p>Confrontos diretos entre equipes</p>
<code>GET /api/games/FM/A/confrontation</code>
</div>
<div class="card">
<h3><span class="icon">&#128205;</span> Locais</h3>
<p>Lista todos os locais de jogos</p>
<code>GET /api/localities</code>
</div>
<div class="card">
<h3><span class="icon">&#128214;</span> Documentacao</h3>
<p>Swagger UI com todos os endpoints</p>
<code>GET /apidocs</code>
</div>
</div>
<div class="footer">NDU Torneio Universitario &middot; <a href="/apidocs">Documentacao Swagger</a></div>
</body>
</html>'''

class MyApp:

  def __init__(self):
        self.service = MyService()
        print("!!!!!!!!!!!!!!!!!!!!! Iniciando MyApp !!!!!!!!!!!!!!!!!!!!!")

# Cria uma instância da classe MyApp
my_app = MyApp()
myAppService = my_app.service
# myAppService = MyService()

@app.route('/api/info', methods=['GET'])
def get_info():
    return json.dumps(myAppService.get_info(), ensure_ascii=False).encode('utf8')

@app.route('/api/flags', methods=['GET'])
def get_flags():
    return json.dumps(myAppService.get_flags(), ensure_ascii=False).encode('utf8')

@app.route('/api/games/<modality>/<series>/confrontation', methods=['GET'])
def get_confrontation(modality, series):
    """
    Obtém informações sobre os confrontos.
    ---
    parameters:
      - name: team1
        in: query
        type: string
        description: Nome do primeiro time.
        required: true
      - name: team2
        in: query
        type: string
        description: Nome do segundo time.
        required: true
      - name: modality
        in: path
        type: string
        description: A modalidade dos jogos.
      - name: series
        in: path
        type: string
        description: A série dos jogos.
    responses:
      200:
        description: Lista de confrontos ou lista do vencedor do confronto.
    """
    try:

      team1_name = request.args.get('team1', type=str)
      team2_name = request.args.get('team2', type=str)

      confrontation = myAppService.get_confrontation(modality, series)
      if team1_name and team2_name:
        return confrontation[team1_name][team2_name]

      return jsonify(confrontation)

    except Exception as e:
        return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)

@app.route('/api/games/<modality>/<series>/clashes', methods=['GET'])
def get_clashes(modality, series):
    """
    Obtém informações de confronto entre dois times.
    ---
    parameters:
      - name: team1
        in: query
        type: string
        description: Nome do primeiro time.
        required: true
      - name: team2
        in: query
        type: string
        description: Nome do segundo time.
        required: true
      - name: modality
        in: path
        type: string
        description: A modalidade dos jogos.
      - name: series
        in: path
        type: string
        description: A série dos jogos.
    responses:
      200:
        description: Informações de confronto entre os dois times.
      404:
        description: Pelo menos um dos times não foi encontrado.
    """
    try:

      if 'team1' not in request.args or 'team2' not in request.args:
        raise MissingParameterError("Os parâmetros 'team1' e 'team2' são obrigatórios.")
       
      team1_name = request.args.get('team1', type=str)
      team2_name = request.args.get('team2', type=str)

      df_clashes = myAppService.list_clashes(team1_name, team2_name, modality, series)
      return jsonify(df_clashes.to_dict(orient='records'))
    
    except MissingParameterError as e:
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)
    
@app.errorhandler(MissingParameterError)
def handle_missing_parameter_error(error):
    response = jsonify({'error': str(error)})
    response.status_code = 400
    return response

@app.route('/api/games/<modality>/<series>', methods=['GET'])
def get_games(modality, series):
    """
    Obtém informações sobre os jogos por time.
    ---
    parameters:
    - name: modality
      in: path
      type: string
      description: A modalidade dos jogos.
    - name: series
      in: path
      type: string
      description: A série dos jogos.
    responses:
      200:
        description: Lista de jogos.
    """
    try:

      team_query = request.args.get('team')
      simulator_query = request.args.get('simulator')

      if simulator_query :
        df_games = myAppService.get_simulator_games(modality, series)
      else:
        df_games = myAppService.get_games_by_team(modality, series, team_query)
      return json.dumps(df_games, ensure_ascii=False).encode('utf8')

    except Exception as e:
        return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)

@app.route('/api/playoff/<modality>/<series>', methods=['GET'])
def get_playoff(modality, series):
    """
    Obtém informações sobre os playoffs .
    ---
    parameters:
    - name: modality
      in: path
      type: string
      description: A modalidade dos jogos.
    - name: series
      in: path
      type: string
      description: A série dos jogos.
    responses:
      200:
        description: Lista de jogos.
    """
    try:

      df_games = myAppService.get_playoff_games(modality, series)
      return json.dumps(df_games, ensure_ascii=False).encode('utf8')

    except Exception as e:
        return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)
    
@app.route('/api/nextGames/local/<local>', methods=['GET'])
def get_games_by_local(local):
    try:
        all_games = myAppService.get_next_games_by_local(local)
        return jsonify(all_games)
    except Exception as e:
        return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)

    
@app.route('/api/modalities', methods=['GET'])
def get_modalities():
    """
    Obtém informações sobre os jogos por time.
    ---
    parameters:
    - name: modality
      in: path
      type: string
      description: A modalidade dos jogos.
    - name: series
      in: path
      type: string
      description: A série dos jogos.
    responses:
      200:
        description: Lista de jogos.
    """
    try:
      modalities = myAppService.generate_all_modalities()
      return modalities
    except Exception as e:
        return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)
    
@app.route('/api/localities', methods=['GET'])
def get_localities():
    """
    Obtém informações sobre os locais dos jogos.
    responses:
      200:
        description: Lista de localidades.
    """
    try:
      modalities = myAppService.generate_all_localities()
      return modalities
    except Exception as e:
        return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)

@app.route('/api/ranking/<modality>/<series>', methods=['GET'])
def get_all_rankings(modality, series):
    """
    Obtém os rankings de todos os grupos.
    ---
    parameters:
      - name: simulator
        in: query
        type: boolean
        description: Indica se é para obter o ranking do simulador.
      - name: modality
        in: path
        type: string
        description: A modalidade para a qual o ranking deve ser obtido.
      - name: series
        in: path
        type: string
        description: A série para a qual o ranking deve ser obtido.
    responses:
      200:
        description: Rankings de todos os grupos.
    """
    try:
      simulator = request.args.get('simulator', type=bool)
      group_query = request.args.get('group')

      if group_query:
        df_group = myAppService.get_df_ranking_group(group_query, modality, series)
        return df_group

      all_rankings = myAppService.generate_all_rankings(modality, series)

      return all_rankings
      
    except Exception as e:
      return jsonify({'error': getattr(e, 'message', str(e))}), getattr(e, 'errorCode', 500)
      
if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('PORT', 5001))
    app.run(debug=debug, port=port)