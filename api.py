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
<div class="footer"><a href="/simulator" style="font-size:1rem;font-weight:600">&#9917; Abrir Simulador de Jogos</a><br><br>NDU Torneio Universitario &middot; <a href="/apidocs">Documentacao Swagger</a></div>
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

@app.route('/simulator')
def simulator_page():
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NDU - Simulador de Jogos</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
.top-bar{background:#1e293b;border-bottom:1px solid #334155;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10}
.top-bar h1{font-size:1.2rem;font-weight:700;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.top-bar a{color:#38bdf8;text-decoration:none;font-size:.85rem}
.container{max-width:1100px;margin:0 auto;padding:20px}
.controls{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;align-items:center}
select{background:#1e293b;border:1px solid #334155;color:#e2e8f0;padding:10px 16px;border-radius:8px;font-size:.9rem;cursor:pointer}
select:focus{outline:none;border-color:#38bdf8}
.btn{padding:10px 20px;border-radius:8px;border:none;font-size:.85rem;font-weight:600;cursor:pointer;transition:all .2s}
.btn-primary{background:#38bdf8;color:#0f172a}.btn-primary:hover{background:#7dd3fc}
.btn-secondary{background:#334155;color:#e2e8f0}.btn-secondary:hover{background:#475569}
.btn-success{background:#22c55e;color:#fff}.btn-success:hover{background:#4ade80}
.columns{display:grid;grid-template-columns:1fr 380px;gap:20px}
@media(max-width:900px){.columns{grid-template-columns:1fr}}
.section{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;margin-bottom:16px}
.section h2{font-size:1rem;color:#94a3b8;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.game-card{background:#0f172a;border:1px solid #334155;border-radius:10px;padding:14px;margin-bottom:10px;transition:border-color .2s}
.game-card:hover{border-color:#475569}
.game-card .meta{font-size:.75rem;color:#64748b;margin-bottom:8px;display:flex;gap:12px}
.game-row{display:flex;align-items:center;gap:10px;justify-content:center}
.team-name{flex:1;font-size:.9rem;font-weight:500;text-align:right}
.team-name.away{text-align:left}
.score-input{width:48px;height:40px;text-align:center;font-size:1.1rem;font-weight:700;background:#1e293b;border:2px solid #334155;border-radius:8px;color:#e2e8f0}
.score-input:focus{outline:none;border-color:#38bdf8}
.score-input.played{background:#334155;color:#94a3b8;border-color:transparent}
.vs{color:#475569;font-weight:700;font-size:.85rem}
.played-badge{font-size:.7rem;background:#334155;color:#94a3b8;padding:2px 8px;border-radius:4px}
.sim-badge{font-size:.7rem;background:rgba(56,189,248,.15);color:#38bdf8;padding:2px 8px;border-radius:4px}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th{text-align:left;padding:8px 10px;color:#64748b;border-bottom:1px solid #334155;font-weight:600;font-size:.75rem;text-transform:uppercase}
td{padding:8px 10px;border-bottom:1px solid #1e293b}
tr:hover td{background:rgba(56,189,248,.03)}
.pos{font-weight:700;color:#475569;width:24px;text-align:center}
.pos.q{color:#22c55e}
.team-cell{font-weight:600;color:#f1f5f9}
.pts{font-weight:800;color:#38bdf8;font-size:1rem}
.group-title{font-size:.85rem;font-weight:700;color:#818cf8;margin:16px 0 8px;padding-bottom:6px;border-bottom:1px solid #334155}
.loading{text-align:center;padding:40px;color:#64748b}
.tab-group{display:flex;gap:4px;margin-bottom:16px}
.tab{padding:8px 16px;border-radius:8px;border:1px solid #334155;background:transparent;color:#94a3b8;cursor:pointer;font-size:.8rem;transition:all .2s}
.tab.active{background:#38bdf8;color:#0f172a;border-color:#38bdf8;font-weight:600}
.filter-row{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.filter-btn{padding:4px 12px;border-radius:6px;border:1px solid #334155;background:transparent;color:#94a3b8;cursor:pointer;font-size:.75rem}
.filter-btn.active{background:#334155;color:#e2e8f0}
</style>
</head>
<body>
<div class="top-bar">
<h1>NDU Simulador</h1>
<a href="/">&#8592; Voltar</a>
</div>
<div class="container">
<div class="controls">
<select id="modality">
<option value="">Carregando...</option>
</select>
<button class="btn btn-primary" onclick="loadData()">Carregar</button>
<button class="btn btn-success" onclick="calculateRanking()">Calcular Ranking</button>
<button class="btn btn-secondary" onclick="randomize()">Preencher Aleatorio</button>
<button class="btn btn-secondary" onclick="clearSim()">Limpar Simulacao</button>
</div>
<div class="columns">
<div id="games-col">
<div class="section">
<h2>&#9917; Jogos</h2>
<div class="filter-row" id="group-filters"></div>
<div id="games-list"><div class="loading">Selecione uma modalidade</div></div>
</div>
</div>
<div id="ranking-col">
<div class="section">
<h2>&#128200; Classificacao</h2>
<div id="ranking-tables"><div class="loading">Carregue os jogos primeiro</div></div>
</div>
</div>
</div>
</div>
<script>
const API=window.location.origin;
let allGames=[], rankings={}, activeGroup='all';

async function init(){
  const res=await fetch(API+'/api/modalities');
  const mods=await res.json();
  const sel=document.getElementById('modality');
  sel.innerHTML=mods.map(m=>`<option value="${m.value}">${m.label}</option>`).join('');
  loadData();
}

async function loadData(){
  const mod=document.getElementById('modality').value;
  if(!mod)return;
  const [m,s]=mod.split('/');
  const res=await fetch(API+`/api/games/${m}/${s}`);
  allGames=await res.json();
  // Load rankings
  try{
    const rRes=await fetch(API+`/api/ranking/${m}/${s}`);
    rankings=await rRes.json();
  }catch(e){rankings={}}
  renderGroupFilters();
  renderGames();
  calculateRanking();
}

function renderGroupFilters(){
  const groups=[...new Set(allGames.map(g=>g.GRUPO).filter(Boolean))].sort();
  const div=document.getElementById('group-filters');
  div.innerHTML=`<button class="filter-btn ${activeGroup==='all'?'active':''}" onclick="setGroup('all')">Todos</button>`+
    groups.map(g=>`<button class="filter-btn ${activeGroup===g?'active':''}" onclick="setGroup('${g}')">Grupo ${g}</button>`).join('');
}

function setGroup(g){activeGroup=g;renderGames()}

function renderGames(){
  const div=document.getElementById('games-list');
  let games=activeGroup==='all'?allGames:allGames.filter(g=>g.GRUPO===activeGroup);
  // Sort: simulator games first
  games=[...games].sort((a,b)=>(a.SIMULADOR===b.SIMULADOR?0:a.SIMULADOR?-1:1));
  div.innerHTML=games.map((g,i)=>{
    const idx=allGames.indexOf(g);
    const isSim=g.SIMULADOR;
    const gm=isSim?'':'played';
    const ro=isSim?'':'readonly';
    const badge=isSim?'<span class="sim-badge">Simular</span>':'<span class="played-badge">Realizado</span>';
    return `<div class="game-card">
      <div class="meta"><span>${g.DIA||'A definir'}</span><span>${g.HORARIO||''}</span><span>${g.LOCAL||''}</span><span>Grupo ${g.GRUPO||'?'}</span>${badge}</div>
      <div class="game-row">
        <span class="team-name">${g.Mandante}</span>
        <input type="number" min="0" max="99" class="score-input ${gm}" id="home-${idx}" value="${isSim?'':g.GOLS_MANDANTE}" ${ro} onchange="calculateRanking()">
        <span class="vs">X</span>
        <input type="number" min="0" max="99" class="score-input ${gm}" id="away-${idx}" value="${isSim?'':g.GOLS_VISITANTE}" ${ro} onchange="calculateRanking()">
        <span class="team-name away">${g.Visitante}</span>
      </div>
    </div>`}).join('');
}

function calculateRanking(){
  // Build ranking from zero + games
  const groups={};
  // Init from rankings data or from games
  allGames.forEach(g=>{
    if(!g.GRUPO)return;
    if(!groups[g.GRUPO])groups[g.GRUPO]={};
    [g.Mandante,g.Visitante].forEach(t=>{
      if(!groups[g.GRUPO][t])groups[g.GRUPO][t]={Time:t,Pontos:0,Jogos:0,V:0,E:0,D:0,Gols_Pro:0,Gols_Contra:0,Saldo:0};
    });
  });
  // Calculate from all games
  allGames.forEach((g,i)=>{
    if(!g.GRUPO)return;
    const gr=groups[g.GRUPO];if(!gr)return;
    const home=gr[g.Mandante],away=gr[g.Visitante];
    if(!home||!away)return;
    let gh,ga;
    if(g.SIMULADOR){
      const hEl=document.getElementById('home-'+i);
      const aEl=document.getElementById('away-'+i);
      if(!hEl||!aEl)return;
      gh=parseInt(hEl.value);ga=parseInt(aEl.value);
      if(isNaN(gh)||isNaN(ga))return;
    }else{
      gh=parseInt(g.GOLS_MANDANTE);ga=parseInt(g.GOLS_VISITANTE);
      if(isNaN(gh)||isNaN(ga))return;
    }
    home.Jogos++;away.Jogos++;
    home.Gols_Pro+=gh;home.Gols_Contra+=ga;
    away.Gols_Pro+=ga;away.Gols_Contra+=gh;
    home.Saldo=home.Gols_Pro-home.Gols_Contra;
    away.Saldo=away.Gols_Pro-away.Gols_Contra;
    if(gh>ga){home.Pontos+=3;home.V++;away.D++}
    else if(gh<ga){away.Pontos+=3;away.V++;home.D++}
    else{home.Pontos+=1;away.Pontos+=1;home.E++;away.E++}
  });
  renderRanking(groups);
}

function renderRanking(groups){
  const div=document.getElementById('ranking-tables');
  const sorted=Object.keys(groups).sort();
  div.innerHTML=sorted.map(g=>{
    const teams=Object.values(groups[g]).sort((a,b)=>b.Pontos-a.Pontos||b.Saldo-a.Saldo||b.Gols_Pro-a.Gols_Pro);
    return `<div class="group-title">Grupo ${g}</div>
    <table><tr><th>#</th><th>Time</th><th>P</th><th>J</th><th>V</th><th>E</th><th>D</th><th>GP</th><th>GC</th><th>SG</th></tr>
    ${teams.map((t,i)=>`<tr>
      <td class="pos ${i<2?'q':''}">${i+1}</td>
      <td class="team-cell">${t.Time}</td>
      <td class="pts">${t.Pontos}</td>
      <td>${t.Jogos}</td><td>${t.V}</td><td>${t.E}</td><td>${t.D}</td>
      <td>${t.Gols_Pro}</td><td>${t.Gols_Contra}</td><td>${t.Saldo}</td>
    </tr>`).join('')}</table>`}).join('');
}

function randomize(){
  allGames.forEach((g,i)=>{
    if(!g.SIMULADOR)return;
    const h=document.getElementById('home-'+i);
    const a=document.getElementById('away-'+i);
    if(h&&a){h.value=Math.floor(Math.random()*6);a.value=Math.floor(Math.random()*6)}
  });
  calculateRanking();
}

function clearSim(){
  allGames.forEach((g,i)=>{
    if(!g.SIMULADOR)return;
    const h=document.getElementById('home-'+i);
    const a=document.getElementById('away-'+i);
    if(h&&a){h.value='';a.value=''}
  });
  calculateRanking();
}

init();
</script>
</body>
</html>'''

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