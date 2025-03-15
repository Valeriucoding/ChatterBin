import pyaudio
import numpy as np
import tempfile
import os
import wave
import whisper
import requests
import json
import time
import io
from pydub import AudioSegment
from pydub.playback import play

# Import functions from the original voice assistant
from voice_assistant import record_audio, transcribe_with_whisper, call_ai_api

def speak_with_elevenlabs(text, voice_id="pNInz6obpgDQGcFmaJgB", api_key=None):
    """
    Convert text to speech using ElevenLabs API and play the audio.
    
    Args:
        text (str): The text to convert to speech
        voice_id (str): The ElevenLabs voice ID to use
        api_key (str): Your ElevenLabs API key. If None, will look for ELEVENLABS_API_KEY env variable
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Get API key from environment if not provided
    if api_key is None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            print("Error: ElevenLabs API key not found. Please set the ELEVENLABS_API_KEY environment variable.")
            return False
    
    # ElevenLabs API endpoint
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    # Headers with API key
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    # Request data
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "language_code": "ro",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        print("Generating speech with ElevenLabs...")
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            # Convert audio bytes to an audio segment
            audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
            
            # Send a POST request with the audio length
            try:
                dummy_url = "http://192.168.10.47"
                audio_length_ms = len(audio)
                payload = {
                    "audio_length_ms": audio_length_ms,
                    "audio_length_sec": audio_length_ms / 1000
                }
                requests.post(dummy_url, json=payload, timeout=1)
                print(f"Sent audio length: {audio_length_ms/1000:.2f} seconds")
            except Exception as e:
                print(f"Failed to send audio length: {str(e)}")
            
            # Play the audio
            print("Speaking...")
            play(audio)
            return True
        else:
            print(f"Error: ElevenLabs API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error using ElevenLabs API: {str(e)}")
        return False

def process_voice_command_with_speech(recording_duration=5, whisper_model="small"):
    """Record audio, transcribe it, send to AI API, and speak the response."""
    # Record audio
    audio_path = record_audio(duration=recording_duration)
    
    # Transcribe audio
    transcription = transcribe_with_whisper(audio_path, model_name=whisper_model)
    print(f"You said: {transcription}")
    
    # Send to AI API
    print("Getting response...")
    response = call_ai_api(transcription)
    
    # Process response
    if "error" in response:
        ai_message = f"Error: {response['error']}"
    else:
        try:
            # Extract the AI's response from the JSON
            ai_message = response.get("choices", [{}])[0].get("message", {}).get("content", "No response")
        except (KeyError, IndexError):
            ai_message = f"Error: Unexpected response format from API."
    
    # Print and speak the response
    print(f"\nAI: {ai_message}")
    speak_with_elevenlabs(ai_message)
    
    return ai_message

def main():
    print("ElevenLabs Voice-Activated AI Assistant")
    print("Say 'exit' to quit the program")
    print("======================================")
    
    # Check for API key
    if not os.environ.get("ELEVENLABS_API_KEY"):
        print("Warning: ELEVENLABS_API_KEY environment variable not found.")
        print("Please set your ElevenLabs API key with:")
        print("export ELEVENLABS_API_KEY='your-api-key'")
        api_key = input("Or enter your ElevenLabs API key now: ").strip()
        if api_key:
            os.environ["ELEVENLABS_API_KEY"] = api_key
        else:
            print("No API key provided. Exiting.")
            return

    while True:
        try:
            # Process voice command and speak response
            ai_response = process_voice_command_with_speech(recording_duration=5)
            
            # Check if the user wants to exit
            if "exit" in ai_response.lower():
                print("Exiting program. Goodbye!")
                break
                
            # Wait a bit before the next recording
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nProgram interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
    
if __name__ == "__main__":
    main()
