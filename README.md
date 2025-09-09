
# espeak-ai-mimic
espeak-ai-mimic is a tool for mimicking espeak behavior and calling OpenAI API-compatible endpoints for text-to-speech (TTS), mainly used for Renpy's custom self-voice feature.

## Background
Renpy's self-voice feature relies on the espeak command. This tool intercepts espeak calls, forwards the text to a local or remote TTS API (such as an OpenAI-compatible endpoint), and automatically plays the generated speech. <b>LINUX ONLY!</b>

## Features
- Supports configuring different voices and speeds for roles via `voice_mapping.txt`.
- Automatically splits long text and generates speech sentence by sentence.
- Supports audio file caching to avoid repeated generation.
- Logs all processed text.
- Compatible with Renpy's command-line invocation.

## Usage
1. Start a local TTS API service, like [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI), edit `API_URL` in `espeak.py` if needed.
2. Configure `voice_mapping.txt` in the following format:
	```
	# name voice_name speed
	default am_michael 1.1
	you am_eric 1
	```
	Then edit `VOICE_MAPPING` in `espeak.py` to point to your `voice_mapping.txt`.

	`voice_name` for [Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI) can be found at [VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).
3. Point Renpy's espeak command to this script (e.g., via symlink or replacement).
	```bash
	sudo ln -s /absolute/path/to/espeak-ai-mimic/espeak.py /usr/bin/espeak
	sudo chmod +x /usr/bin/espeak
	```
	This requires you to uninstall espeak first.
4. Example usage:
	```bash
	python3 espeak.py "default: Hello, world!"
	```
	Or via standard input:
	```bash
	python3 espeak.py
	# Input text, end with Ctrl+D
	```
5. For Renpy games:

   Simply press <kbd>v</kbd> to enable self-voice.
   
   [demo.webm](https://github.com/user-attachments/assets/615f2639-eb5e-40be-8e57-af270c0f04ce)

   
## File Description
- `espeak.py`: Main program, handles text-to-speech logic.
- `voice_mapping.txt`: Role voice and speed mapping table.

## Dependencies
- Python 3
- requests
- ffmpeg (for audio playback)

Install dependencies:
```bash
pip install requests
sudo apt-get install ffmpeg
```

## API Compatibility
By default, calls `http://localhost:8880/v1/audio/speech`. You can modify `API_URL` as needed.

## Contributing
Feel free to submit issues or PRs to improve this project.

## License
MIT
