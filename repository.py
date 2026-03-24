import os
import json
from datetime import datetime, timedelta


def _load_json(filepath):
    """Carrega um arquivo JSON, retorna None se não existir."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


class LocalRepository:
    """Repository que lê dados de arquivos JSON locais (pasta files/)."""

    def __init__(self, base_dir='files'):
        self.base_dir = base_dir

    def _mod_path(self, modality, series):
        """Monta o caminho: files/FM/A/ ou files/FF/B/"""
        return os.path.join(self.base_dir, modality, series)

    def get_info(self):
        return _load_json(os.path.join(self.base_dir, 'info.json')) or {}

    def get_flags(self):
        return _load_json(os.path.join(self.base_dir, 'flags.json')) or {}

    def get_confrontation(self, modality, series):
        path = os.path.join(self._mod_path(modality, series), 'confrontation.json')
        return _load_json(path) or {}

    def get_ranking(self, modality, series):
        group_dir = os.path.join(self._mod_path(modality, series), 'group')
        if not os.path.exists(group_dir):
            return {}

        rankings = {}
        for filename in sorted(os.listdir(group_dir)):
            if filename.startswith('ranking_') and filename.endswith('.json') and 'zero' not in filename:
                group_letter = filename.replace('ranking_', '').replace('.json', '')
                data = _load_json(os.path.join(group_dir, filename))
                if data:
                    rankings[group_letter] = data

        # Se não tem rankings calculados, usar os zeros
        if not rankings:
            for filename in sorted(os.listdir(group_dir)):
                if filename.startswith('ranking_zero_') and filename.endswith('.json'):
                    group_letter = filename.replace('ranking_zero_', '').replace('.json', '')
                    data = _load_json(os.path.join(group_dir, filename))
                    if data:
                        rankings[group_letter] = data
        return rankings

    def get_games(self, modality, series):
        path = os.path.join(self._mod_path(modality, series), 'games.json')
        return _load_json(path) or []

    def get_playoff_games(self, modality, series):
        path = os.path.join(self._mod_path(modality, series), 'playoff.json')
        return _load_json(path) or []

    def get_games_by_team(self, modality, series, team=None):
        games = self.get_games(modality, series)
        if team:
            return [g for g in games if g.get('Mandante') == team or g.get('Visitante') == team]
        return games

    def get_ranking_by_group(self, modality, series, group):
        path = os.path.join(self._mod_path(modality, series), 'group', f'ranking_{group}.json')
        data = _load_json(path)
        if data:
            return data
        # Fallback para ranking zero
        path_zero = os.path.join(self._mod_path(modality, series), 'group', f'ranking_zero_{group}.json')
        return _load_json(path_zero) or []

    def get_next_games_by_local(self, local):
        all_games = []
        modalities = [
            ("FM", ["A", "B", "C", "D", "E", "F"]),
            ("FC", ["B", "C"]),
        ]
        for mod, series_list in modalities:
            for s in series_list:
                games = self.get_games(mod, s)
                if games:
                    for game_data in games:
                        if self.check_date_between_week(game_data.get('DIA')) and game_data.get('LOCAL') == local:
                            game_data['modalidade'] = f'{mod}/{s}'
                            all_games.append(game_data)
        return all_games

    def is_date_between(self, date_str, initial_date_str, final_date_str):
        if date_str:
            try:
                date = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
                initial_date = datetime.strptime(initial_date_str, '%Y-%m-%d')
                final_date = datetime.strptime(final_date_str, '%Y-%m-%d')
                return initial_date <= date <= final_date
            except (ValueError, TypeError):
                return False
        return False

    def check_date_between_week(self, date_str):
        current_date = datetime.now()
        initial_date = current_date - timedelta(days=1)
        final_date = current_date + timedelta(days=6 - current_date.weekday())
        if current_date.weekday() == 6:
            final_date = current_date
        return self.is_date_between(date_str, initial_date.strftime('%Y-%m-%d'), final_date.strftime('%Y-%m-%d'))
