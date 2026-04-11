from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import random
import os
from dotenv import load_dotenv
from genius import search_artist, get_songs, pick_weighted_song, get_lyrics, pick_two_lines, change_one_word
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=FileResponse)
def index():
    return "static/index.html"

@app.get("/game")
def game(artist: str):
    songs = get_songs(artist)
    picked = pick_weighted_song(songs)
    lyrics = get_lyrics(picked["url"])
    two_lines = pick_two_lines(lyrics)
    
    if two_lines is None:
        return {"error": "Could not fetch lyrics, try again"}
    
    line_to_change = random.randint(0, 1)
    two_lines_original = two_lines.copy()
    fake_line = change_one_word(two_lines[line_to_change])
    two_lines[line_to_change] = fake_line
    
    original_words = [w.strip(".,!?\"'") for w in two_lines_original[line_to_change].split()]
    fake_words = [w.strip(".,!?\"'") for w in fake_line.split()]
    changed = [w for w in fake_words if w not in original_words]
    changed_word = changed[0] if changed else "unknown"
    
    return {
        "line1": two_lines[0],
        "line2": two_lines[1],
        "changed_line": line_to_change,
        "changed_word": changed_word,
        "original_line": two_lines_original[line_to_change],
        "song": picked["title"],
        "artist": picked["artist"]
    }