import csv
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")

def get_movie_details(title, year):
    base_url = 'https://api.themoviedb.org/3/search/movie'
    params = {
        'api_key': API_KEY,
        'query': title,
        'year': year
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            movie_id = results[0]['id']
            movie_url = f'https://api.themoviedb.org/3/movie/{movie_id}'
            movie_params = {'api_key': API_KEY}
            movie_response = requests.get(movie_url, params=movie_params)
            if movie_response.status_code == 200:
                movie_data = movie_response.json()
                runtime = movie_data.get('runtime', 'N/A')
                genres = ', '.join([genre['name'] for genre in movie_data.get('genres', [])]) or 'N/A'

                # Fetch MPAA rating (U.S. certification)
                release_info_url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates"
                release_info_response = requests.get(release_info_url, params=movie_params)
                if release_info_response.status_code == 200:
                    for release in release_info_response.json().get('results', []):
                        if release['iso_3166_1'] == 'US':
                            for release_detail in release['release_dates']:
                                if 'certification' in release_detail and release_detail['certification']:
                                    return runtime, release_detail['certification'], genres
                return runtime, 'N/A', genres
    return 'N/A', 'N/A', 'N/A'

def get_letterboxd_rating(letterboxd_uri):
    url = letterboxd_uri
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        rating_element = soup.find('meta', {'name': 'twitter:data2'})
        if rating_element:
            return rating_element['content'].split(' ')[0]
        if rating_element:
            return rating_element.text.strip()
    return 'N/A'

# Read the input CSV file
input_file = 'ratings.csv'
output_file = 'ratings_with_details.csv'

with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames + ['Runtime (minutes)', 'MPAA Rating', 'Genres', 'Letterboxd Rating']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        title = row['Name']
        year = row['Year']
        letterboxd_uri = row['Letterboxd URI']  # Basic slug formatting for Letterboxd
        runtime, mpaa_rating, genres = get_movie_details(title, year)
        letterboxd_rating = get_letterboxd_rating(letterboxd_uri)
        print(f"{title} ({year}) - Runtime: {runtime}, MPAA: {mpaa_rating}, Genres: {genres}, Letterboxd: {letterboxd_rating}")
        row['Runtime (minutes)'] = runtime
        row['MPAA Rating'] = mpaa_rating
        row['Genres'] = genres
        row['Letterboxd Rating'] = letterboxd_rating
        writer.writerow(row)

print(f"Processing complete. Results written to {output_file}")