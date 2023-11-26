import json
import logging
from pathlib import Path
from collections import Counter


class SpotifyDataAnalyser:
    def __init__(self):
        prompter = Prompter()
        self.is_extended_data = prompter.prompt_for_extended_data()
        self.datasets_count = None

        self.dataset_path = Path(
            'data/streaming_extended') if self.is_extended_data else Path('data/streaming')
        if not self.is_extended_data:
            self.datasets_count = prompter.prompt_for_dataset_count()

        self.results_amount = prompter.prompt_for_results_amount()

        self.data = DataLoader(self.dataset_path)
        self.data_analyser = DataAnalyser(self.data, self.is_extended_data)

    def main(self):
        AnalyticsGenerator(self.data).execute_spotify_data_analyser(
            self.is_extended_data, self.datasets_count, self.results_amount, self.dataset_path)


class Prompter:
    def __init__(self):
        self.is_extended_data = None
        self.datasets_range = range(1, 4)
        self.datasets_count = None
        self.results_amount = None
        self.max_results_amount = 100

    def prompt_for_input(self, prompt_message, error_message, condition):
        print(prompt_message)
        while True:
            user_input = input().lower()
            if condition(user_input):
                return user_input
            print(error_message)

    def prompt_for_extended_data(self):
        self.is_extended_data = self.prompt_for_input(
            'Do you want to fetch extended data? (y/n)',
            "Invalid choice. Please enter 'y' or 'n'.",
            lambda x: x in ['y', 'yes', 'n', 'no']
        )
        return self.is_extended_data == 'y' or self.is_extended_data == 'yes'

    def prompt_for_dataset_count(self):
        self.datasets_count = self.prompt_for_input(
            f'How many datasets do you want to analyze? ({
                self.datasets_range.start}-{self.datasets_range.stop - 1})',
            f"Invalid choice. Please enter a number between {
                self.datasets_range.start} and {self.datasets_range.stop - 1}.",
            lambda x: x.isdigit() and int(x) in self.datasets_range
        )
        return int(self.datasets_count)

    def prompt_for_results_amount(self):
        self.results_amount = self.prompt_for_input(
            f'How many results do you want to display? (1-{
                self.max_results_amount})',
            f'Invalid choice. Please enter a number between 1 and {
                self.max_results_amount}.',
            lambda x: x.isdigit() and int(x) in range(1, 101)
        )
        return int(self.results_amount)


class DataLoader:
    def __init__(self, path):
        self.path = path
        self.data = None

    def load_data(self, is_extended_data, datasets_count, dataset_path):
        if is_extended_data:
            return self.load_extended_data(dataset_path)
        else:
            return self.load_non_extended_data(datasets_count, dataset_path)

    def load_non_extended_data(self, datasets_count, dataset_path):
        for i in range(datasets_count):
            file_path = dataset_path / f'StreamingHistory{i}.json'
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        yield from json.load(file)
                except json.JSONDecodeError:
                    logging.error(f"Could not decode JSON from {file_path}.")
                    raise
            else:
                logging.error(f"File {file_path} not found.")
                raise FileNotFoundError(f"File {file_path} not found.")

    def load_extended_data(self, dataset_path):
        json_files = list(Path(dataset_path).glob('*.json'))
        for file_path in json_files:
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        for item in data:
                            if item['master_metadata_track_name'] is not None and item['master_metadata_album_artist_name'] is not None and item['master_metadata_album_album_name'] is not None:
                                yield item['master_metadata_track_name'], item['master_metadata_album_artist_name'], item['master_metadata_album_album_name']
                except json.JSONDecodeError:
                    logging.error(f"\nCould not decode JSON from {file_path}.")
            else:
                logging.error(f"\nFile {file_path} not found.")
                raise FileNotFoundError(f"\nFile {file_path} not found.")


class DataAnalyser:
    def __init__(self, data, is_extended_data):
        self.data = data
        self.is_extended_data = is_extended_data
        self.field_map = {
            'trackName': self.get_most_played_tracks,
            'artistName': self.get_most_listened_artists,
            'albumName': self.get_most_listened_albums
        }

    def get_counter(self, field):
        if self.is_extended_data:
            field_index = {
                'trackName': 0,
                'artistName': 1,
                'albumName': 2
            }
            values = [item[field_index[field]] for item in self.data]
            return Counter(values)
        else:
            return Counter(item[field] for item in self.data)

    def get_most_played_tracks(self):
        return self.get_counter('trackName')

    def get_most_listened_artists(self):
        return self.get_counter('artistName')

    def get_most_listened_albums(self):
        return self.get_counter('albumName')


class AnalyticsGenerator:
    def __init__(self, data):
        self.data = data

    def display_analytics(self, counts, results_amount, label):
        print(f"\nTop {results_amount} {label}s:")
        print(f"{'-' * 45}")
        print(f"{label.ljust(35)} | Count")
        print(f"{'-' * 45}")
        for item, count in counts.most_common(results_amount):
            trimmed_item = (item[:24] + '...') if len(item) > 35 else item
            print(f"{trimmed_item.ljust(35)} | {count}")
        print(f"{'-' * 45}\n")

    def execute_spotify_data_analyser(self, is_extended_data, datasets_count, results_amount, dataset_path):
        try:
            data = list(self.data.load_data(
                is_extended_data, datasets_count, dataset_path))
            self.data_analyser = DataAnalyser(data, is_extended_data)
            print(f"\nAnalyzing {len(data)} tracks...\n")
            self.display_analytics(
                self.data_analyser.get_most_played_tracks(), results_amount, "Track")
            self.display_analytics(
                self.data_analyser.get_most_listened_artists(), results_amount, "Artist")
            if is_extended_data:
                self.display_analytics(
                    self.data_analyser.get_most_listened_albums(), results_amount, "Album")
        except (Exception) as e:
            print(f'\n{e}')


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    logging.info("Starting Spotify Data Analyser...")
    spotify_data_analyser = SpotifyDataAnalyser().main()
    logging.info("Spotify Data Analyser analysed and data displayed.")
