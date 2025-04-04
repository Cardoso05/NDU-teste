
import tabula
import pandas as pd
import os
from datetime import datetime
import logging
import inspect
import modules.utils as utils
import modules.check as check
import modules.fixes as fixes
import requests
from lxml import html
from datetime import datetime

# Função para obter e analisar o Boletim Oficial
from lxml import html
import re
import shutil
import os


data_hora_atual = datetime.now()

dia_atual = data_hora_atual.date()

# Configuração básica de logging
# logging.basicConfig(filename='logs/log_ndu_' + data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S") + '.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(filename='logs/debug_ndu_' + data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S") + '.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_function_entry():
    function_name = inspect.currentframe().f_back.f_code.co_name
    logging.debug(f"Function: {function_name}")

# Criando tabela dos grupos
def create_zero_ranking_group(table_groups, filepath):
    log_function_entry()
    dataframes = []
    
    header_zero = table_groups.columns[0]
    if 'grupo' not in header_zero.lower():
        logging.warning(f"header_zero inválido: {header_zero}")
        logging.info("Colocando o header atual na última linha")
        # Adicionar os cabeçalhos atuais à última linha de valores de cada coluna
        table_groups.loc[len(table_groups)+1] = table_groups.columns

        num_cols = table_groups.shape[1]
        new_headers = [f'Grupo {chr(65 + i)}' for i in range(num_cols)]

        logging.info("Atualizando headers")
        # Atualizar os cabeçalhos do DataFrame
        table_groups.columns = new_headers

    for group in ['Grupo A', 'Grupo B', 'Grupo C']:
        if group in table_groups:
            teams = table_groups[group].tolist()

            # Criar DataFrame vazio com as colunas necessárias
            columns = ['Time', 'Pontos', 'Jogos', 'V', 'E', 'D', 'Gols_Pro', 'Gols_Contra', 'Saldo']
            df_group = pd.DataFrame(columns=columns)
            
            # Adicionar nomes dos grupos
            df_group['Time'] = teams

            # Inicializar outras colunas com zeros
            for col in columns[1:]:
                df_group[col] = 0

            # Define o tipo de dados para as colunas
            dtypes = {'Pontos': int, 'Jogos': int, 'V': int, 'E': int, 'D': int, 'Gols_Pro': int, 'Gols_Contra': int, 'Saldo': int}
            df_group = df_group.astype(dtypes)
            df_group['ID'] = [utils.generate_game_id() for _ in range(len(df_group))]

            # Adicionar DataFrame à lista
            dataframes.append((group, df_group))

            # Salvar em JSON
            group_letter = group.split()[-1]
            json_data = df_group.to_dict(orient='records')
            utils.create_json(json_data, f"{filepath}/ranking_zero_{group_letter}.json")
        
    return dataframes

# Formatando tabela de jogos
def check_simulador(row):
    # log_function_entry()
    
    dia_jogo = pd.to_datetime(row['DIA'], format='%Y-%m-%d', errors='coerce').date()

    if pd.isna(dia_jogo) or dia_jogo > dia_atual or row['PLACAR'] == 'X':
        row['PLACAR'] = 'X'
        row['GOLS_MANDANTE'] = ''
        row['GOLS_VISITANTE'] = ''
        return True
    else:
        return False   
    
def verify_empty_games(tables):
    log_function_entry()
    for df in tables:
        # Verificar se 'EQUIPE Mandante' é NaN
        empty_rows = df[df['EQUIPE Mandante'].isna()]

        # Remover as linhas onde 'EQUIPE Mandante' ou 'EQUIPE Visitante' é NaN
        if not empty_rows.empty:
            df.dropna(subset=['EQUIPE Mandante'], inplace=True)
    
    concatenated_df = pd.concat(tables, ignore_index=True)
    return concatenated_df

def generate_table_games(tables):
    log_function_entry()
    tb_games = verify_empty_games(tables)
    df_games = pd.DataFrame(tb_games)
    if df_games['DIA'].isna().all():
        df_games['DIA'] = ''
    else:
        # Limpar os espaços extras e formatar a coluna 'DIA'
        df_games['DIA'] = df_games['DIA'].str.replace(' ', '', regex=False)
        df_games['DIA'] = pd.to_datetime(df_games['DIA'] + '/' + pd.to_datetime('now', utc=True).strftime('%Y'), format='%d/%m/%Y', errors='coerce')

    # Limpar os espaços extras e corrigir a formatação dos placares
    df_games['PLACAR'] = df_games['PLACAR'].str.replace(' ', '', regex=True)
    df_games[['GOLS_MANDANTE', 'GOLS_VISITANTE']] = df_games['PLACAR'].str.split('X', expand=True)
    df_games['ID'] = [utils.generate_game_id() for _ in range(len(df_games))]
    df_games.rename(columns={'HORÁRIO': 'HORARIO'}, inplace=True)
    df_games.rename(columns={'EQUIPE Mandante': 'Mandante'}, inplace=True)
    df_games.rename(columns={'EQUIPE Visitante': 'Visitante'}, inplace=True)
    df_games['SIMULADOR'] = df_games.apply(check_simulador, axis=1)
    return df_games

# Jogos por time
def listar_jogos_por_time(df_games, team_surname):
    log_function_entry()
    condition_home = df_games['EQUIPE Mandante'].str.contains(team_surname)
    condition_away = df_games['EQUIPE Visitante'].str.contains(team_surname)
    games_by_team = df_games[condition_home | condition_away]
    return games_by_team

def listar_confrontos(df_games, teamOne, teamTwo):
    log_function_entry()
    # Filtrar os jogos onde a equipe é a mandante ou visitante
    condition_home = df_games['EQUIPE Mandante'].str.contains(teamOne)
    condition_away = df_games['EQUIPE Visitante'].str.contains(teamOne)

    # Combinar as condições usando o operador lógico OR (|)
    games_teamOne = df_games[condition_home | condition_away]

    # Filtrar os jogos onde a outra equipe é a visitante
    games_between_home = games_teamOne[games_teamOne['EQUIPE Mandante'].str.contains(teamTwo)]
    if games_between_home.empty == False:
      return games_between_home
    else:
      return games_teamOne[games_teamOne['EQUIPE Visitante'].str.contains(teamTwo)]

# TODO - Confronto direto
def update_confronto_direto(winner_team, loser_team, draw, confrontos_diretos):
    log_function_entry()
    if draw:
        resultado = 'E'
    else:
        resultado = winner_team

    # Registrar o resultado no dicionário
    confrontos_diretos.setdefault(winner_team, {}).setdefault(loser_team, resultado)
    confrontos_diretos.setdefault(loser_team, {}).setdefault(winner_team, resultado)
    return confrontos_diretos

# TODO - Confronto direto
def remover_confronto_direto(winner_team, loser_team, confrontos_diretos):
    log_function_entry()
    # Registrar o resultado no dicionário
    confrontos_diretos.setdefault(winner_team, {}).setdefault(loser_team, '')
    confrontos_diretos.setdefault(loser_team, {}).setdefault(winner_team, '')
    return confrontos_diretos

# TODO - Confronto direto
def gerar_confronto_direto(df_games, filepath):
    log_function_entry()
    confrontos_diretos = {}

    # Iterar sobre os jogos e registrar os resultados dos confrontos diretos
    for _, jogo in df_games.iterrows():
      equipe_mandante = jogo['Mandante']
      equipe_visitante = jogo['Visitante']
      placar_mandante = jogo['GOLS_MANDANTE']
      placar_visitante = jogo['GOLS_VISITANTE']

      resultado = ''

      if placar_mandante > placar_visitante:
          resultado = equipe_mandante
      elif placar_mandante < placar_visitante:
          resultado = equipe_visitante
      else:
          resultado = 'E'

      # Registrar o resultado no dicionário
      confrontos_diretos.setdefault(equipe_mandante, {}).setdefault(equipe_visitante, resultado)
      confrontos_diretos.setdefault(equipe_visitante, {}).setdefault(equipe_mandante, resultado)

    utils.create_json(confrontos_diretos, filepath + '/confrontation.json')

    return confrontos_diretos

# TODO - Confronto direto
def confrontos_to_df(confrontos_diretos):
    log_function_entry()
    # Criar um DataFrame a partir dos resultados dos confrontos diretos
    df_confrontos_diretos = pd.DataFrame(confrontos_diretos).T.fillna('').sort_index()
    df_confrontos_diretos.index.name = 'Equipes'
    return df_confrontos_diretos

def tem_ranking(df_group):
    log_function_entry()
    elemento = df_group.iloc[2, 1] # Time na Posição 1o Colocado
    return pd.isna(elemento) == False

def atualizar_classificacao(df_group, df_confrontos_diretos, group):
    log_function_entry()
    linhas_pontos_iguais = df_group[df_group.duplicated(subset='Pontos', keep=False)]
    # Obter apenas os nomes das atléticas
    atléticas_pontos_iguais = linhas_pontos_iguais['Atléticas'].tolist()
    if len(atléticas_pontos_iguais) == 2:
        team_ahead = df_confrontos_diretos.loc[atléticas_pontos_iguais[0], atléticas_pontos_iguais[1]]
        atléticas_pontos_iguais.remove(team_ahead)

        # Nome da atlética que você deseja trocar
        team_behind = atléticas_pontos_iguais[0]

        # Encontrar a posição da atlética no DataFrame
        position_ahead = df_group.index[df_group['Atléticas'] == team_ahead].tolist()[0]
        position_behind = df_group.index[df_group['Atléticas'] == team_behind].tolist()[0]

        # Trocar os valores entre as linhas diretamente
        df_group.loc[position_ahead], df_group.loc[position_behind] = df_group.loc[position_behind].copy(), df_group.loc[position_ahead].copy()

    logging.info(f"Classificação grupo {group} atualizada com confrontos diretos:")

def atualizar_df_games(new_game_data):
    log_function_entry()
    global df_games
    df_games = pd.concat([df_games, pd.DataFrame([new_game_data])], ignore_index=True)

def remover_df_games(matches_to_remove, simulador=True):
    log_function_entry()
    # Obter os índices dos jogos a serem removidos
    indices_to_remove = matches_to_remove.index

    # Remover os jogos do DataFrame original
    df_games.drop(indices_to_remove, inplace=True)

def atualizar_dados_times(df_nova, df_original):
    log_function_entry()
    # Salvar a coluna 'ID' em uma variável temporária
    id_column = df_original.pop('ID')

    # Redefinir o índice do DataFrame df_original
    df_original.reset_index(inplace=True)

    # Atualizar os dados em df_original com base em df_nova
    for index, row in df_nova.iterrows():
        log_function_entry()
        time = row['Time']
        idx = df_original[df_original['Time'] == time].index
        if not idx.empty:
            df_original.loc[idx[0]] = row

    # Reatribuir a coluna 'ID' ao DataFrame df_original
    df_original['ID'] = id_column

    # Agora, df_original contém os dados atualizados
    return df_original

def get_rankings_zero_group(modality):
    log_function_entry()
    
    # Diretório base dos arquivos de ranking
    directory = f'files/{modality}/group'
    
    # Dicionário para armazenar os rankings
    rankings = {}
    
    # Listando os arquivos no diretório
    for filename in os.listdir(directory):
        if filename.startswith('ranking_zero_') and filename.endswith('.json'):
            group = filename[len('ranking_zero_'):-len('.json')]
            filepath = os.path.join(directory, filename)
            rankings[group] = utils.load_json_data(filepath)
    
    return rankings

def get_index_teams(rankings):
    log_function_entry()
    
    index_teams = {}
    
    for group, ranking_list in rankings.items():
        index_teams[group] = {time_dict['Time']: index for index, time_dict in enumerate(ranking_list)}
    
    return index_teams

def generate_ranking_by_games(modality):
    log_function_entry()
    
    json_games = utils.load_json_data(f'files/{modality}/games.json')
    rankings = get_rankings_zero_group(modality)
    index_teams = get_index_teams(rankings)

    # Percorra cada jogo no DataFrame df_games
    for jogo in json_games:
        if jogo["PLACAR"] == "X":
            continue
        grupo = jogo["GRUPO"]
        mandante = jogo["Mandante"]
        visitante = jogo["Visitante"]
        dados_ranking_mandante = rankings[grupo][index_teams[grupo][mandante]]
        dados_ranking_visitante = rankings[grupo][index_teams[grupo][visitante]]
        placar_mandante = int(jogo["GOLS_MANDANTE"]) 
        placar_visitante = int(jogo["GOLS_VISITANTE"])
        
        # Atualize os pontos das equipes com base no resultado do jogo
        if placar_mandante > placar_visitante:
            dados_ranking_mandante['Pontos'] = int(dados_ranking_mandante['Pontos']) + 3
            dados_ranking_mandante['V'] = int(dados_ranking_mandante['V']) + 1
            dados_ranking_visitante['D'] = int(dados_ranking_visitante['D']) + 1
            
        
        elif placar_mandante == placar_visitante:
            dados_ranking_mandante['Pontos'] = int(dados_ranking_mandante['Pontos']) + 1
            dados_ranking_visitante['Pontos'] = int(dados_ranking_visitante['Pontos']) + 1
            dados_ranking_mandante['E'] = int(dados_ranking_mandante['E']) + 1
            dados_ranking_visitante['E'] = int(dados_ranking_visitante['E']) + 1
            
        else:
            dados_ranking_visitante['Pontos'] = int(dados_ranking_visitante['Pontos']) + 3
            dados_ranking_visitante['V'] = int(dados_ranking_visitante['V']) + 1
            dados_ranking_mandante['D'] = int(dados_ranking_mandante['D']) + 1

        dados_ranking_mandante['Jogos'] = int(dados_ranking_mandante['Jogos']) + 1
        dados_ranking_visitante['Jogos'] = int(dados_ranking_visitante['Jogos']) + 1
        
        
        dados_ranking_mandante['Gols_Pro'] = int(dados_ranking_mandante['Gols_Pro']) + placar_mandante
        dados_ranking_visitante['Gols_Pro'] = int(dados_ranking_visitante['Gols_Pro']) + placar_visitante
        
        dados_ranking_mandante['Gols_Contra'] = int(dados_ranking_mandante['Gols_Contra']) + placar_visitante
        dados_ranking_visitante['Gols_Contra'] = int(dados_ranking_visitante['Gols_Contra']) + placar_mandante

        dados_ranking_mandante['Saldo'] = int(dados_ranking_mandante['Gols_Pro']) - int(dados_ranking_mandante['Gols_Contra'])
        dados_ranking_visitante['Saldo'] = int(dados_ranking_visitante['Gols_Pro']) - int(dados_ranking_visitante['Gols_Contra'])
        
    return rankings

def update_ranking(rankings, df_confrontos_diretos):
    log_function_entry()
    df_groups = []
    idx = 1
    columns_to_convert = ['Pontos', 'Jogos', 'V', 'E', 'D', 'Gols_Pro', 'Gols_Contra', 'Saldo']
  
    for group, tb_group in rankings.items():
        df_group = pd.DataFrame(tb_group)
        df_group[columns_to_convert] = df_group[columns_to_convert].astype(int)
        df_group.sort_values(by=['Pontos', 'Saldo', 'Gols_Pro'], ascending=[False, False, False], inplace=True)
        df_group.reset_index(drop=True, inplace=True)
        pontos_iguais = df_group['Pontos'].unique().tolist()

        for ponto in pontos_iguais:
            times_pontos_iguais = df_group[df_group['Pontos'] == ponto]['Time'].tolist()
            if len(times_pontos_iguais) == 2:
                team_ahead = df_confrontos_diretos.loc[times_pontos_iguais[0], times_pontos_iguais[1]]
                if team_ahead != 'E' and team_ahead != '':
                    times_pontos_iguais.remove(team_ahead)

                    # Nome da atlética que você deseja trocar
                    team_behind = times_pontos_iguais[0]

                    # Encontrar a posição da atlética no DataFrame
                    position_ahead = df_group.index[df_group['Time'] == team_ahead].tolist()[0]
                    position_behind = df_group.index[df_group['Time'] == team_behind].tolist()[0]
                    if position_ahead > position_behind:
                        # Trocar os valores entre as linhas diretamente
                        df_group.loc[position_ahead], df_group.loc[position_behind] = df_group.loc[position_behind].copy(), df_group.loc[position_ahead].copy()
                        logging.info(f"Classificação grupo {chr(idx + 64)} atualizada com confrontos diretos:")
                        logging.info(f'Por confronto direto: 1º {team_ahead} 2º {team_behind}')
                
        df_groups.append(df_group)
        idx = idx + 1
    return df_groups

def format_tb_group(tb_group):
    log_function_entry()
    header_zero = tb_group.columns[0]
    if 'grupo' not in header_zero.lower():
        logging.warning(f"header_zero inválido: {header_zero}")
        logging.info("Colocando o header atual na última linha")
        # Adicionar os cabeçalhos atuais à última linha de valores de cada coluna
        tb_group.loc[len(tb_group)+1] = tb_group.columns

        num_cols = tb_group.shape[1]
        new_headers = [f'Grupo {chr(65 + i)}' for i in range(num_cols)]

        logging.info("Atualizando headers")
        # Atualizar os cabeçalhos do DataFrame
        tb_group.columns = new_headers
    return tb_group

# TODO - Exceções
def format_DIA_HORARIO(games_data):
    log_function_entry()
    if 'DIA HORÁRIO' in games_data.columns:
        current_year = datetime.datetime.now().year

        def process_date_time(value):
            if value.strip() != "":
                value_strip = value[:6].strip()
                value_fmt = value_strip.replace(" ", "")
                value_with_year = f"{value_fmt}/{current_year}"
                date = pd.to_datetime(value_with_year, format='%d/%m/%Y', errors='coerce').date()
                time = value.replace(value_strip, '').strip().replace(" ", "")
                return date, time
            else:
                return pd.NaT, ''

        # Aplicar a função à coluna "DIA HORÁRIO" apenas se o campo 'DIA' não for NaT e o campo 'HORARIO' não for NaN
        games_data[['DIA', 'HORARIO']] = games_data.apply(lambda row: process_date_time(row['DIA HORÁRIO']) if pd.isna(row['DIA']) and pd.isna(row['HORARIO']) else (row['DIA'], row['HORARIO']), axis=1).apply(pd.Series)
        games_data.drop(columns=['DIA HORÁRIO'], inplace=True)

    return games_data

# TODO - Exceções
def format_LOCAL_GRUPO(games_data):
    log_function_entry()
    if 'LOCAL GRUPO' in games_data.columns:

        def process_date_time(value):
            if value.strip() != "":
                value_strip = value[:-1].strip()  # Remove o último caractere
                local = value_strip.strip()  # Aplica trim ao local
                group = value[-1]  # Último caractere como group
                return local, group
            else:
                return pd.NaT, pd.NaT

        # Aplicar a função à coluna "DIA HORÁRIO" apenas se o campo 'DIA' não for NaT e o campo 'HORARIO' não for NaN
        games_data[['LOCAL', 'GRUPO']] = games_data.apply(lambda row: process_date_time(row['LOCAL GRUPO']) if pd.isna(row['LOCAL']) and pd.isna(row['GRUPO']) else (row['LOCAL'], row['GRUPO']), axis=1).apply(pd.Series)
        games_data.drop(columns=['LOCAL GRUPO'], inplace=True)

    return games_data

def preencher_simulador(df):
    log_function_entry()
    for index, row in df.iterrows():
        dia_jogo = pd.to_datetime(row['DIA'], format='%Y-%m-%d', errors='coerce').date()
        if pd.isna(dia_jogo) or dia_jogo > dia_atual or row['PLACAR'] == 'X':
            df.at[index, 'PLACAR'] = 'X'
            df.at[index, 'GOLS_MANDANTE'] = ''
            df.at[index, 'GOLS_VISITANTE'] = ''
            df.at[index, 'SIMULADOR'] = True
    
    return df

def get_all_teams_by_rankings(rankings):
    teams = [team['Time'] for group in rankings.values() for team in group]
    return teams

def execute_update_games_by_modality(modality, pages):
    logging.info(f"Modalidade: {modality}")
    tables = tabula.read_pdf("files/Boletim.pdf", pages=pages)
    rankings_zero_group = get_rankings_zero_group(modality)
    teams = get_all_teams_by_rankings(rankings_zero_group)
    tb_games = [tables[1], tables[2]]
    filepath = f'files/{modality}'
    df_games = generate_table_games(tb_games)
    df_games = fixes.corrigir_times(teams, df_games)
    df_games = fixes.corrigir_local(df_games)
    df_games = fixes.corrigir_horario(df_games)
    df_games = fixes.corrigir_dia(df_games)
    df_games = preencher_simulador(df_games)
    utils.create_files(df_games, filepath)
    check.check_game_data(modality)

def execute_update_data_by_modality(modality, pages):
    log_function_entry()
    logging.info(f"Modalidade: {modality}")
    tables = tabula.read_pdf("files/Boletim.pdf", pages=pages)
    rankings_zero_group = get_rankings_zero_group(modality)
    teams = get_all_teams_by_rankings(rankings_zero_group)
    tb_games = [tables[1], tables[2]]

    filepath = f'files/{modality}'
    df_games = generate_table_games(tb_games)
    df_games = fixes.corrigir_times(teams, df_games)
    df_games = fixes.corrigir_local(df_games)
    df_games = fixes.corrigir_horario(df_games)
    df_games = fixes.corrigir_dia(df_games)
    df_games = preencher_simulador(df_games)
    utils.create_files(df_games, filepath)
    
    confrontos = gerar_confronto_direto(df_games, filepath)
    df_confrontos_diretos = confrontos_to_df(confrontos)
    rankings = generate_ranking_by_games(modality)
    df_groups = update_ranking(rankings, df_confrontos_diretos)

    idx_char = 65 # Letra A
    for df_group in df_groups:
        utils.create_json_from_df(df_group, f'files/{modality}/group/ranking_{chr(idx_char)}.json')
        idx_char = idx_char + 1
    
    check.check_game_data(modality)
    # create_backup_zipped(modality)

def execute_update_data(dic_modalities_page):
    log_function_entry()
    utils.extract_and_save_team_names(dic_modalities_page)
    for item in dic_modalities_page:
        # Cada item é um dicionário com uma única chave-valor
        modality, details = next(iter(item.items()))
        group_page_range = details['group_page_range']
        execute_update_data_by_modality(modality, group_page_range)
        logging.info("----------------------------------------")
    
    utils.create_backup_zipped()

def update_ranking_by_games(modality):
    log_function_entry()
    filepath = f'files/{modality}'
    df_games = pd.read_json(f'{filepath}/games.json')

    confrontos = gerar_confronto_direto(df_games, filepath)
    df_confrontos_diretos = confrontos_to_df(confrontos)
    rankings = generate_ranking_by_games(modality)
    df_groups = update_ranking([rankings['A'], rankings['B']], df_confrontos_diretos)
    df_groupA = df_groups[0]
    df_groupB = df_groups[1]

    df_groupA.to_csv(f'files/{modality}/group/ranking_A.csv', index=False)
    df_groupB.to_csv(f'files/{modality}/group/ranking_B.csv', index=False)

    utils.csv_to_json(f'files/{modality}/group/ranking_A.csv', f'files/{modality}/group/ranking_A.json')
    utils.csv_to_json(f'files/{modality}/group/ranking_B.csv', f'files/{modality}/group/ranking_B.json')

def execute_update_games(dic_modalities_page):
    log_function_entry()
    for item in dic_modalities_page:
        # Cada item é um dicionário com uma única chave-valor
        modality, details = next(iter(item.items()))
        group_page_range = details['group_page_range']
        execute_update_games_by_modality(modality, group_page_range)
        logging.info("----------------------------------------")

def find_date_boletim(text_boletim):
    padrao_data = r'\d{2}/\d{2}/\d{4}'
    match = re.search(padrao_data, text_boletim)
    if match:
        data_inicio = match.group(0)
        logging.info(f"Data do boletim: {data_inicio}")
        return data_inicio
    else:
        print("Data do boletim não encontrada no texto.")

def find_link_boletim(tree):
    # Localizar o elemento <a> com o XPath específico e obter o valor do atributo href
    href_boletim = tree.xpath('/html/body/div[4]/ul[1]/li[1]/a/@href')
    if href_boletim:
        link_href = href_boletim[0]
        logging.info(f"Link do Boletim Oficial: {link_href}")
        return link_href
    else:
        logging.error("Não foi possível obter o valor do atributo href.")

def save_pdf_by_url(site_data, caminho_destino):
    # Faz a solicitação HTTP para obter o conteúdo do PDF
    resposta = requests.get(
            site_data["url"],
            headers=site_data["headers"],
            cookies=site_data["cookies"],
            stream=True)

    # Verifica se a solicitação foi bem-sucedida
    if resposta.status_code == 200:
        # Abre o arquivo para escrita em modo binário
        with open(caminho_destino, 'wb') as arquivo:
            # Copia o conteúdo da resposta para o arquivo
            shutil.copyfileobj(resposta.raw, arquivo)
        logging.info("Boletim baixado com sucesso!")
    else:
        logging.error(f"Falha ao baixar o arquivo. Código de status: {resposta.status_code}")

def update_boletim_file():
    # Script Python para obter e analisar o Boletim Oficial():
    # Caminho da pasta "files" dentro do diretório do projeto
    pasta_destino = os.path.join(os.getcwd(), "files")

    # Nome do arquivo a ser salvo
    nome_arquivo = "Boletim.pdf"

    # Caminho completo para salvar o arquivo
    caminho_destino = os.path.join(pasta_destino, nome_arquivo)

    try:
        boletim_ndu_site_data = {
            "url": "https://www.ndu.net.br/boletim",
            "headers": {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "referer": "https://www.google.com/",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            },
            "cookies": {
                "PHPSESSID": "b6ad2300bff8498ec189b940c7f15790",
                "ci_session": "a%3A5%3A%7Bs%3A10%3A%22session_id%22%3Bs%3A32%3A%2298fbfe38a71333c43dc41c0a7580011d%22%3Bs%3A10%3A%22ip_address%22%3Bs%3A33%3A%222801%3Aa4%3A102%3A5%3Aa510%3Abf1a%3Ace17%3A719d%22%3Bs%3A10%3A%22user_agent%22%3Bs%3A111%3A%22Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F134.0.0.0%20Safari%2F537.36%22%3Bs%3A13%3A%22last_activity%22%3Bi%3A1743548826%3Bs%3A9%3A%22user_data%22%3Bs%3A0%3A%22%22%3B%7D2df0baf46ac3d77906c1b80989b9cbe4"
            }
        }

        response = requests.get(
            boletim_ndu_site_data["url"],
            headers=boletim_ndu_site_data["headers"],
            cookies=boletim_ndu_site_data["cookies"]
        )
        response.raise_for_status()  # Lança uma exceção se a resposta tiver um código de status de erro

        # Parsear o HTML usando lxml
        tree = html.fromstring(response.content)

        # Localizar o elemento <a> com o XPath específico
        link_boletim = tree.xpath('/html/body/div[4]/ul[1]/li[1]/a')

        if link_boletim:
            link_texto = link_boletim[0].text

            # Verificar se o texto contém "Boletim Oficial"
            if "Boletim Oficial" in link_texto:
                logging.info(f"Boletim Oficial encontrado: {link_texto}")
                find_date_boletim(link_texto)
                href_boletim = find_link_boletim(tree)
                boletim_ndu_site_data["url"] = href_boletim
                save_pdf_by_url(boletim_ndu_site_data, caminho_destino)
            else:
                print("O texto do link não contém 'Boletim Oficial'.")
        else:
            print("Elemento <a> não encontrado no XPath especificado.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao obter o HTML: {e}")
    except Exception as e:
        logging.error(f"Ocorreu um erro inesperado: {e}")