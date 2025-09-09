#!/usr/bin/python3

import sys
import datetime
import os
import re
import requests
import uuid
import subprocess
import tempfile
import time
import hashlib

LOG_FILE = os.path.expanduser("~/espeak_log.txt")
AUDIO_DIR = os.path.expanduser("~/espeak_audio")
API_URL = "http://localhost:8880/v1/audio/speech"
VOICE_MAPPING = "~/espeak-ai-mimic/voice_mapping.txt"
VOICE = "am_michael"  # Default voice
MODEL = "kokoro"  # Default model
SPEED = 1  # Default speed
USE_SPLIT = False  # Whether to split long text


# Read voice_map and speed_map from voice_mapping.txt
def load_voice_mapping(filename):
    global VOICE, SPEED
    voice_map = {}
    speed_map = {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    name, voice, speed = parts[0].lower(), parts[1], parts[2]
                    voice_map[name] = voice
                    try:
                        speed_map[name] = float(speed)
                    except ValueError:
                        speed_map[name] = SPEED
    except Exception as e:
        print(f"Failed to read voice_mapping.txt: {e}")
    if "default" in voice_map:
        VOICE = voice_map["default"]
    if "default" in speed_map:
        SPEED = speed_map["default"]
    return voice_map, speed_map


voice_map, speed_map = load_voice_mapping(
    os.path.join(
        os.path.dirname(__file__),
        os.path.expanduser(VOICE_MAPPING),
    )
)

# Create audio save directory
os.makedirs(AUDIO_DIR, exist_ok=True)


def log_text(text):
    """Write text to log file"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n")


def split_text(text):
    """Split text by punctuation"""
    text = text.replace("\n", " ")
    text = text.replace('"', "")
    # Add special marker after punctuation, then split
    marked_text = re.sub(r"([.?!])", r"\1[SPLIT]", text)
    segments = marked_text.split("[SPLIT]")
    segments = [s.strip() for s in segments]
    segments = [s for s in segments if s and s != " "]

    # Filter empty strings and strip whitespace
    segments = [segment.strip() for segment in segments if segment.strip()]
    return segments


def tts_api_call(text, voice=VOICE):
    """Call TTS API to convert text to speech"""
    try:
        response = requests.post(
            API_URL,
            json={
                "model": MODEL,
                "input": text,
                "voice": voice_map.get(voice, VOICE),
                "response_format": "mp3",
                "speed": speed_map.get(voice, SPEED),
            },
        )
        if response.status_code == 200:
            return response.content
        else:
            print(f"API call failed, status code: {response.status_code}")
            print(f"Error message: {response.text}")
            return None
    except Exception as e:
        print(f"API call exception: {str(e)}")
        return None


def save_audio(audio_data, md5_hash):
    """Save audio file"""
    if not audio_data:
        return None

    # Generate unique filename
    filename = f"{md5_hash}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    # Save audio file
    with open(filepath, "wb") as f:
        f.write(audio_data)

    print(f"Audio saved: {filepath}")
    return filepath


def play_audio(filepath):
    """Play audio file"""
    try:
        # Use ffplay to play (silent mode)
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath]
        )
    except Exception as e:
        print(f"Error playing audio: {str(e)}")


def process_text(text):
    """Process text: log, split, TTS, play"""
    # Log original text
    log_text(text)

    # Split text
    if USE_SPLIT:
        segments = split_text(text)
    else:
        segments = [text]

    print(f"Text split into {len(segments)} segments")

    # Process each segment
    for i, segment in enumerate(segments):
        if not segment:
            continue
        # Check if any ASCII characters in segment, if not, skip it
        if not re.search(r"[a-zA-Z0-9]", segment):
            print(f"Skip non-ASCII segment: {segment}")
            continue
        # Skip prefixes like "-a 100 "
        prefix_skip_list = [
            "-a \d+ ",
        ]
        for prefix in prefix_skip_list:
            if re.match(prefix, segment):
                segment = re.sub(prefix, "", segment).strip()

        print(f"Processing segment {i+1}/{len(segments)}: {segment}")
        # md5 hash of text
        md5_hash = hashlib.md5(segment.encode("utf-8")).hexdigest()
        print(f"MD5 hash of segment {i+1}: {md5_hash}")
        # Generate audio filename
        audio_filepath = os.path.join(AUDIO_DIR, f"{md5_hash}.mp3")
        if os.path.exists(audio_filepath):
            print(f"Audio file already exists, skip generation: {audio_filepath}")
            play_audio(audio_filepath)
            continue

        # Call API to generate speech
        if re.match(r"\w+\: ", segment):
            voice = segment.split(":")[0].lower()
            segment = segment.split(":", 1)[1].strip().strip('"')
        else:
            voice = "default"
        audio_data = tts_api_call(segment, voice=voice)

        # Save audio file
        save_audio(audio_data, md5_hash)
        if audio_data:
            play_audio(audio_filepath)
            # Wait for audio to finish playing before processing next segment
            time.sleep(0.2)  # Add short delay to avoid audio overlap


def main():
    """Main function, process command line arguments or stdin"""
    # Check if there are command line arguments
    if len(sys.argv) > 1:
        # pkill ffplay
        subprocess.run(["pkill", "ffplay"])
        time.sleep(0.2)  # Ensure ffplay is terminated
        # Join all arguments into a string
        text = " ".join(sys.argv[1:])
        process_text(text)
    else:
        # No arguments, read from stdin
        print("Input text (end with Ctrl+D):")
        for line in sys.stdin:
            line = line.strip()
            if line:  # Ignore empty lines
                process_text(line)


if __name__ == "__main__":
    main()
