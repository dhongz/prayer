from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)
from app.schemas.prayers import PrayerText
from app.config import config

async def transcribe_audio(audio_file: str) -> PrayerText:
    """
    Transcribe audio file using Deepgram's API
    Returns a PrayerText object containing the transcribed text
    """
    try:
        # Create Deepgram client
        deepgram = DeepgramClient(config.DEEPGRAM_API_KEY)
        
        # Read the audio file
        with open(audio_file, "rb") as file:
            buffer_data = file.read()
            
        payload: FileSource = {
            "buffer": buffer_data,
        }
        
        # Configure Deepgram options
        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
        )
        
        # Get transcription
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
        
        # Extract transcribed text from response
        print(response)
        transcribed_text = response.results.channels[0].alternatives[0].transcript
        
        return PrayerText(text=transcribed_text)
        
    except Exception as e:
        raise Exception(f"Transcription error: {str(e)}")