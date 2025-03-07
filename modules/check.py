
import logging
from modules.utils import load_json_data, log_function_entry


def check_game_data(modality, filaname='games'):
    log_function_entry()
    file_path = f'files/{modality}/{filaname}.json'
    json_data = load_json_data(file_path)
    
    # Verifica o formato dos campos 'DIA' e 'HORARIO' para cada jogo
    for json_game in json_data:
        if len(str(json_game['DIA'])) != 10:
            logging.critical(f"Jogo {json_game['ID']} com DIA inválido: {json_game['DIA']}")
        if len(str(json_game['HORARIO'])) > 8:
            logging.critical(f"Jogo {json_game['ID']} com HORARIO inválido: {json_game['HORARIO']}")
