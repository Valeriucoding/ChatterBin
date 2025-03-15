import pyaudio
import numpy as np
import tempfile
import os
import wave
import whisper
import requests
import json
import time

def record_audio(duration=5, sample_rate=16000):
    """Record audio from the microphone for a specified duration."""
    print(f"Listening for {duration} seconds...")
    
    # Audio recording parameters
    channels = 1
    chunk = 1024
    audio_format = pyaudio.paInt16
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Open stream
    stream = p.open(
        format=audio_format,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=chunk
    )
    
    frames = []
    
    # Record audio
    for i in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    print("Processing...")
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    
    with wave.open(temp_file.name, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(audio_format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
    
    return temp_file.name

def transcribe_with_whisper(audio_path, model_name="small"):
    """Transcribe audio file using OpenAI's Whisper model."""
    # Load the Whisper model
    model = whisper.load_model(model_name)
    
    # Transcribe with Romanian language setting
    result = model.transcribe(audio_path, language="ro")
    
    # Clean up the temporary file
    os.unlink(audio_path)
    
    return result["text"]

def call_ai_api(user_message):
    """Call the AI API with the user's message and return the response."""
    url = "https://ai.hackclub.com/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
"messages": [
    {"role": "user", "content": user_message},
   {"role": "system", "content": "Răspunde ca un coș de gunoi sarcastic și amuzant, jignind in gluma pe cel cu care vorbești, dar într-un mod glumeț, folosind maximum 2-3 propoziții. Raspunsurile trebuie sa fie total stupide si pe langa, sa nu aiba nicio legatura cu viata reala"}
]

    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}

def process_voice_command(recording_duration=5, whisper_model="base"):
    """Record audio, transcribe it, send to AI API, and return response."""
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
        return f"Error: {response['error']}"
    else:
        try:
            # Extract the AI's response from the JSON
            ai_message = response.get("choices", [{}])[0].get("message", {}).get("content", "No response")
            return ai_message
        except (KeyError, IndexError):
            return f"Error: Unexpected response format from API. Raw response: {response}"

def main():
    print("Voice-Activated AI Assistant")
    print("Say 'exit' to quit the program")
    print("==============================")
    
    while True:
        try:
            # Process voice command
            ai_response = process_voice_command()
            print(f"\nAI: {ai_response}")
            
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
