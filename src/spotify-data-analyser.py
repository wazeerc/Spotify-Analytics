import json
import logging
from pathlib import Path
from collections import Counter


class SpotifyDataAnalyser:
    def __init__(self):
        self.is_extended_data = Prompter().prompt_for_extended_data()
        self.datasets_count = None

        if self.is_extended_data:
            self.dataset_path = Path('data/streaming_extended')
        else:
            self.dataset_path = Path('data/streaming')
            self.datasets_count = Prompter().prompt_for_dataset_count()

        self.results_amount = Prompter().prompt_for_results_amount()

        self.data = DataLoader(self.dataset_path)
        self.data_analyser = DataAnalyser(self.data, self.is_extended_data)

    def main(self):
        AnalyticsGenerator(self.data).execute_spotify_data_analyser(
            self.is_extended_data, self.datasets_count, self.results_amount, self.dataset_path)

#! To fix prompts, if one prompt is invalid, it should keep prompting until a valid input is given, this is not currently the case.


class Prompter:
    def __init__(self):
        self.is_extended_data = None
        self.datasets_range = range(1, 4)
        self.datasets_count = None
        self.results_amount = None

    def prompt_for_extended_data(self):
        print("Do you also want to analyze extended data? (y/n)")
        while True:
            user_input = input().lower()
            if user_input in ['y', 'yes']:
                self.is_extended_data = True
            elif user_input in ['n', 'no']:
                self.is_extended_data = False
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")
            return self.is_extended_data

    def prompt_for_dataset_count(self):
        print(f'How many datasets do you want to analyze? ({
              self.datasets_range.start}-{self.datasets_range.stop - 1})')
        while True:
            try:
                user_input = int(input())
                if user_input in self.datasets_range:
                    self.datasets_count = user_input
                    return self.datasets_count
                else:
                    print(f"Invalid choice. Please enter a number between ({
                        self.datasets_range.start}-{self.datasets_range.stop - 1}).")
            except ValueError:
                print(f"Invalid choice. Please enter a number between ({
                    self.datasets_range.start}-{self.datasets_range.stop - 1}).")

    def prompt_for_results_amount(self):
        print('How many results do you want to display? (1-100)')
        while True:
            try:
                user_input = int(input())
                if user_input in range(1, 101):
                    self.results_amount = user_input
                    return self.results_amount
                else:
                    print("Invalid choice. Please enter a number between 1 and 100.")
            except ValueError:
                print("Invalid choice. Please enter a number between 1 and 100.")


class DataLoader:
    def __init__(self, path):
        self.path = path
        self.data = None

    def load_data(self, is_extended_data, datasets_count, dataset_path):
        if is_extended_data is False:
            for i in range(datasets_count):
                file_path = dataset_path / f'StreamingHistory{i}.json'
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            yield from json.load(file)
                    except json.JSONDecodeError:
                        logging.error(
                            f"Could not decode JSON from {file_path}.")
                        raise
                else:
                    logging.error(f"File {file_path} not found.")
                    raise FileNotFoundError(f"File {file_path} not found.")
        elif is_extended_data is True:
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
                        logging.error(
                            f"Could not decode JSON from {file_path}.")
                else:
                    logging.error(f"File {file_path} not found.")
                    raise FileNotFoundError(
                        f"File {file_path} not found.")


class DataAnalyser:
    def __init__(self, data, is_extended_data):
        self.data = data
        self.is_extended_data = is_extended_data

    def get_most_played_tracks(self, data):
        if self.is_extended_data:
            track_names, _, _ = zip(*data)
            return Counter(track_names)
        else:
            return Counter((item['trackName'] for item in data))

    def get_most_listened_artists(self, data):
        if self.is_extended_data is True:
            _, artist_names, _ = zip(*data)
            return Counter(artist_names)
        else:
            return Counter((item['artistName'] for item in data))

    def get_most_listened_albums(self, data):
        if self.is_extended_data is True:
            _, _, album_names = zip(*data)
            return Counter(album_names)
        else:
            return Counter((item['albumName'] for item in data))


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
            data = list(self.data.load_data(is_extended_data,
                                            datasets_count, dataset_path))
            self.data_analyser = DataAnalyser(data, is_extended_data)
            print(f"\nAnalyzing {len(data)} tracks...\n")
            self.display_analytics(
                self.data_analyser.get_most_played_tracks(data), results_amount, "Track")
            self.display_analytics(
                self.data_analyser.get_most_listened_artists(data), results_amount, "Artist")
            if is_extended_data is True:
                self.display_analytics(
                    self.data_analyser.get_most_listened_albums(data), results_amount, "Album")
        except Exception as e:
            print(e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    logging.info("Starting Spotify Data Analyser...")
    spotify_data_analyser = SpotifyDataAnalyser().main()
    logging.info("Spotify Data Analyser analysed and data displayed.")
