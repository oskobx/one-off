import requests
import random
from bs4 import BeautifulSoup
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()


# paste your Genius Client Access Token here
TOKEN = os.getenv("GENIUS_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

def search_artist(name):
    url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    params = {"q": name, "per_page": 20}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def get_songs(artist_name):
    data = search_artist(artist_name)
    songs = []
    for hit in data["response"]["hits"]:
        song = hit["result"]
        songs.append({
            "title": song["title"],
            "artist": song["primary_artist"]["name"],
            "views": song["stats"].get("pageviews") or 1,
            "url": song["url"]
        })
    return songs

def pick_weighted_song(songs):
    weights = [s["views"] for s in songs]
    return random.choices(songs, weights=weights, k=1)[0]

def get_lyrics(song_url):
    response = requests.get(song_url)
    soup = BeautifulSoup(response.text, "html.parser")
    containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
    lyrics = []
    for container in containers:
        for line in container.get_text(separator="\n").split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("["):
                continue
            if "Contributors" in line:
                continue
            if line.endswith("Lyrics"):
                continue
            if line == "Read More":
                continue
            if line == "]":
                continue
            lyrics.append(line)
    return lyrics

def pick_two_lines(lyrics):
    if len(lyrics) < 2:
        return None
    start = random.randint(0, len(lyrics) - 2)
    return lyrics[start:start + 2]

def change_one_word(line):
    client = Groq(api_key=GROQ_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""You will receive a lyric line in Polish or English. Your task is to change EXACTLY one single word in it.
                    Rules:
                    - Change only one word, keep all other words identical
                    - The replacement word must be a real Polish or English word
                    - The replacement word should fit grammatically and sound plausible but be subtly wrong
                    - Do not modify parts of words, only replace whole words
                    - Return ONLY the modified line, no explanation, no quotes

                    Lyric line: {line}"""
            }
        ]
    )
    return response.choices[0].message.content.strip()

# --- run it ---
if __name__ == "__main__":
    artist = input("Enter artist name: ")
    songs = get_songs(artist)
    picked = pick_weighted_song(songs)
    print(f"\nPicked: {picked['title']} by {picked['artist']} — {picked['views']} views")
    lyrics = get_lyrics(picked["url"])
    two_lines = pick_two_lines(lyrics)

    line_to_change = random.randint(0, 1)
    two_lines_original = two_lines.copy()
    fake_line = change_one_word(two_lines[line_to_change])
    two_lines[line_to_change] = fake_line

    print("\n--- SPOT THE FAKE WORD ---")
    for i, line in enumerate(two_lines):
        print(f"{i+1}. {line}")

    guess_line = int(input("\nWhich line has the fake word? (1 or 2): "))
    guess_word = input("Which word is fake? Type it: ")

    if guess_line - 1 == line_to_change:
        print("\nCorrect line!")
    else:
        print(f"\nWrong line! The fake was in line {line_to_change + 1}")

    original_words = [w.strip(".,!?\"'") for w in two_lines_original[line_to_change].split()]
    fake_words = [w.strip(".,!?\"'") for w in fake_line.split()]
    changed = [w for w in fake_words if w not in original_words]
    changed_word = changed[0] if changed else "unknown"

    if guess_word.strip(".,!?\"'").lower() == changed_word.strip(".,!?\"'").lower():
        print("Correct word!")
    else:
        print(f"Wrong word! The fake word was: {changed_word}")

    print(f"\nThe original line was: {two_lines_original[line_to_change]}")
    print(f"The fake line was: {fake_line}")