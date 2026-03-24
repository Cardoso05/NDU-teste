
import tabula
import pandas as pd
from datetime import datetime
import logging
import inspect
import os
import modules.utils as utils
import modules.fixes as fixes
import modules.main as main

data_hora_atual = datetime.now()
dia_atual = data_hora_atual.date()

os.makedirs('logs', exist_ok=True)
logging.basicConfig(filename='logs/debug_ndu_' + data_hora_atual.strftime("%Y-%m-%d_%H-%M-%S") + '.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log_function_entry():
    function_name = inspect.currentframe().f_back.f_code.co_name
    logging.debug(f"Function: {function_name}")

def _create_ranking_df(teams):
    """Cria DataFrame de ranking zerado para uma lista de times."""
    columns = ['Time', 'Pontos', 'Jogos', 'V', 'E', 'D', 'Gols_Pro', 'Gols_Contra', 'Saldo']
    df_group = pd.DataFrame(columns=columns)
    df_group['Time'] = teams
    for col in columns[1:]:
        df_group[col] = 0
    dtypes = {'Pontos': int, 'Jogos': int, 'V': int, 'E': int, 'D': int, 'Gols_Pro': int, 'Gols_Contra': int, 'Saldo': int}
    df_group = df_group.astype(dtypes)
    df_group['ID'] = [utils.generate_game_id() for _ in range(len(df_group))]
    return df_group

def _col_names_lower(table):
    """Retorna nomes de colunas em minúsculo."""
    return [str(c).lower() for c in table.columns]

def _has_column_like(table, name):
    """Verifica se tabela tem coluna parecida com 'name' (case-insensitive)."""
    return any(name.lower() in str(c).lower() for c in table.columns)

def _is_group_table(table):
    """Verifica se a tabela é de grupos (tem coluna 'Grupo A', 'Grupo B', 'Grupo Único', etc)."""
    return any('grupo' in str(c).lower() for c in table.columns)

def _is_games_table(table):
    """Verifica se a tabela é de jogos (tem coluna 'EQUIPE Mandante')."""
    return any('equipe' in str(c).lower() and 'mandante' in str(c).lower() for c in table.columns)

def _has_group_or_serie_column(table):
    """Verifica se tabela tem coluna de grupo ou série (case-insensitive)."""
    for c in table.columns:
        cl = str(c).lower()
        if cl in ('grupo', 'série', 'serie'):
            return True
    return False

def _normalize_game_columns(table):
    """Normaliza nomes de colunas de jogos: 'Grupo' -> 'GRUPO', 'SÉRIE' -> 'GRUPO'."""
    rename_map = {}
    for c in table.columns:
        cl = str(c).lower()
        if cl == 'grupo':
            rename_map[c] = 'GRUPO'
        elif cl in ('série', 'serie'):
            rename_map[c] = 'GRUPO'
    if rename_map:
        table = table.rename(columns=rename_map)
    return table


def create_zero_ranking_group(table_groups, filepath):
    log_function_entry()
    dataframes = []

    # Verificar se é Grupo Único
    is_grupo_unico = any('único' in str(c).lower() or 'unico' in str(c).lower() for c in table_groups.columns)

    if is_grupo_unico:
        all_teams = []
        for col in table_groups.columns:
            all_teams.extend(table_groups[col].dropna().tolist())
        all_teams = [t for t in all_teams if t and not any(x in str(t).lower() for x in ['grupo', 'unnamed', '- - -'])]

        df_group = _create_ranking_df(all_teams)
        dataframes.append(('Grupo A', df_group))
        json_data = df_group.to_dict(orient='records')
        utils.create_json(json_data, f"{filepath}/ranking_zero_A.json")
        return dataframes

    # Tabela com múltiplos grupos - limpar colunas Unnamed e juntar em grupos
    # Primeiro, verificar se há colunas Unnamed no meio (FC/C tem 4 colunas: Grupo A, Unnamed, Unnamed, Grupo B)
    group_cols = {}
    current_group = None
    for col in table_groups.columns:
        col_str = str(col)
        if 'grupo' in col_str.lower() and 'unnamed' not in col_str.lower():
            current_group = col_str
            group_cols[current_group] = []
        if current_group:
            group_cols[current_group].append(col)

    # Se encontrou grupos com colunas associadas, juntar os times
    if group_cols:
        for group_name, cols in group_cols.items():
            all_teams = []
            for col in cols:
                all_teams.extend(table_groups[col].dropna().tolist())
            # Filtrar lixo
            all_teams = [t for t in all_teams if t and 'unnamed' not in str(t).lower() and '- - -' not in str(t)]

            if all_teams:
                df_group = _create_ranking_df(all_teams)
                dataframes.append((group_name, df_group))
                # Extrair letra do grupo
                group_letter = group_name.split()[-1] if 'Grupo' in group_name else group_name[-1]
                json_data = df_group.to_dict(orient='records')
                utils.create_json(json_data, f"{filepath}/ranking_zero_{group_letter}.json")
        return dataframes

    # Fallback: lógica original
    header_zero = table_groups.columns[0]
    if 'grupo' not in header_zero.lower():
        logging.warning(f"header_zero inválido: {header_zero}")
        table_groups.loc[len(table_groups)+1] = table_groups.columns
        num_cols = table_groups.shape[1]
        new_headers = [f'Grupo {chr(65 + i)}' for i in range(num_cols)]
        table_groups.columns = new_headers

    for group in ['Grupo A', 'Grupo B', 'Grupo C']:
        if group in table_groups:
            teams = table_groups[group].dropna().tolist()
            teams = [t for t in teams if '- - -' not in str(t)]
            df_group = _create_ranking_df(teams)
            dataframes.append((group, df_group))
            group_letter = group.split()[-1]
            json_data = df_group.to_dict(orient='records')
            utils.create_json(json_data, f"{filepath}/ranking_zero_{group_letter}.json")

    return dataframes


def execute_zero_ranking(dic_modalities_page):
    log_function_entry()
    for item in dic_modalities_page:
        modality, details = next(iter(item.items()))
        group_page_range = details['group_page_range']
        logging.info(f"modalidade: {modality} | group_page: {group_page_range}")
        tables = tabula.read_pdf("files/Boletim.pdf", pages=group_page_range)

        # Encontrar tabela de grupos e tabelas de jogos
        tb_group = None
        for t in tables:
            if _is_group_table(t) and not _is_games_table(t):
                tb_group = t
                break

        tb_games_list = [t for t in tables if _is_games_table(t)]

        if tb_group is None or len(tb_games_list) == 0:
            print(f'[AVISO] {modality} (páginas {group_page_range}): sem tabela de grupos ou jogos. Pulando...')
            logging.warning(f"{modality}: sem dados de fase de grupos.")
            continue

        # Não reformatar se é grupo único ou se já tem formato correto com colunas Unnamed
        is_unico = any('único' in str(c).lower() or 'unico' in str(c).lower() for c in tb_group.columns)
        has_unnamed_mixed = any('unnamed' in str(c).lower() for c in tb_group.columns) and any('grupo' in str(c).lower() for c in tb_group.columns)
        if not is_unico and not has_unnamed_mixed:
            tb_group = fixes.format_tb_group([tb_group])

        print(f'Grupo página: {group_page_range}')
        print(tb_group)

        # Filtrar tabelas de jogos válidas (com coluna grupo/série, case-insensitive)
        tb_games_valid = [t for t in tb_games_list if _has_group_or_serie_column(t)]
        if len(tb_games_valid) == 0:
            print(f'[AVISO] {modality}: jogos sem coluna GRUPO/SÉRIE. Pulando...')
            continue

        # Normalizar colunas ('Grupo' -> 'GRUPO', 'SÉRIE' -> 'GRUPO')
        tb_games_valid = [_normalize_game_columns(t) for t in tb_games_valid]

        filepath = 'files/' + modality
        filepath_group = filepath + '/group'
        create_zero_ranking_group(tb_group, filepath_group)
        rankings_zero_group = main.get_rankings_zero_group(modality)
        teams = main.get_all_teams_by_rankings(rankings_zero_group)
        df_games = main.generate_table_games(tb_games_valid)
        df_games = fixes.corrigir_local(df_games)
        df_games = fixes.corrigir_times(teams, df_games)
        utils.create_files(df_games, filepath)
        main.gerar_confronto_direto(df_games, filepath)
