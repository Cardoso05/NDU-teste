
import tabula
import pandas as pd
from datetime import datetime
import logging
import inspect
import modules.utils as utils
import modules.fixes as fixes
import modules.main as main

data_hora_atual = datetime.now()

dia_atual = data_hora_atual.date()

import os

os.makedirs('logs', exist_ok=True)
logging.basicConfig(filename='logs/debug_ndu_' + data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S") + '.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_function_entry():
    function_name = inspect.currentframe().f_back.f_code.co_name
    logging.debug(f"Function: {function_name}")

def create_zero_ranking_group(table_groups, filepath):
    log_function_entry()
    dataframes = []
    
    header_zero = table_groups.columns[0]
    if 'grupo' not in header_zero.lower():
        logging.warning(f"header_zero inválido: {header_zero}")
        logging.info(f"Colocando o header atual na última linha")
        # Adicionar os cabeçalhos atuais à última linha de valores de cada coluna
        table_groups.loc[len(table_groups)+1] = table_groups.columns

        num_cols = table_groups.shape[1]
        new_headers = [f'Grupo {chr(65 + i)}' for i in range(num_cols)]

        logging.info(f"Atualizando headers")
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

def _is_group_table(table):
    """Verifica se a tabela é de grupos (tem coluna 'Grupo A' ou similar)."""
    return any('Grupo' in str(c) for c in table.columns)

def _is_games_table(table):
    """Verifica se a tabela é de jogos (tem coluna 'EQUIPE Mandante')."""
    return 'EQUIPE Mandante' in table.columns

def _find_games_tables(tables):
    """Filtra apenas tabelas que são de jogos."""
    return [t for t in tables if _is_games_table(t)]

def _find_group_table(tables):
    """Encontra a tabela de grupos."""
    for t in tables:
        if _is_group_table(t):
            return t
    return None

def execute_zero_ranking(dic_modalities_page):
    log_function_entry()
    for item in dic_modalities_page:
        modality, details = next(iter(item.items()))
        group_page_range = details['group_page_range']
        logging.info(f"modalidade: {modality} | group_page: {group_page_range}")
        tables = tabula.read_pdf("files/Boletim.pdf", pages=group_page_range)

        # Encontrar tabela de grupos e tabelas de jogos
        tb_group = _find_group_table(tables)
        tb_games_list = _find_games_tables(tables)

        if tb_group is None or len(tb_games_list) == 0:
            print(f'[AVISO] {modality} (páginas {group_page_range}): sem tabela de grupos ou jogos na fase de grupos. '
                  f'Provavelmente já está na fase de playoffs. Pulando...')
            logging.warning(f"{modality}: sem dados de fase de grupos. Provavelmente em playoffs.")
            continue

        tb_group = fixes.format_tb_group([tb_group])
        print('Grupo página:', group_page_range)
        print(tb_group)

        # Filtrar apenas tabelas de jogos que tenham coluna GRUPO (não FASE)
        tb_games_with_grupo = [t for t in tb_games_list if 'GRUPO' in t.columns]
        if len(tb_games_with_grupo) == 0:
            print(f'[AVISO] {modality}: jogos encontrados mas sem coluna GRUPO (pode ser playoff). Pulando...')
            continue

        filepath = 'files/' + modality
        filepath_group = filepath + '/group'
        create_zero_ranking_group(tb_group, filepath_group)
        rankings_zero_group = main.get_rankings_zero_group(modality)
        teams = main.get_all_teams_by_rankings(rankings_zero_group)
        df_games = main.generate_table_games(tb_games_with_grupo)
        df_games = fixes.corrigir_local(df_games)
        df_games = fixes.corrigir_times(teams, df_games)
        utils.create_files(df_games, filepath)
        main.gerar_confronto_direto(df_games, filepath)

# dic_modalities_page = utils.get_current_dic_modalities_page()

# execute_zero_ranking(dic_modalities_page)