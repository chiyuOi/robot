#!/usr/bin/env python3
"""
Edge TTS (Text-to-Speech) Output - MULTILINGUAL
Reads LLM response from file and generates/plays speech using Microsoft Edge TTS
Auto-detects language and selects appropriate voice
Supports 100+ languages and accents
"""

import os
import sys
import time
import asyncio
import edge_tts
from typing import Optional

# Paths for inter-process communication
LLM_RESPONSE_FILE = "/tmp/llm_response.txt"
AUDIO_OUTPUT_FILE = "/tmp/speech_output.mp3"
DETECTED_LANGUAGE_FILE = "/tmp/detected_language.txt"

# Comprehensive Edge TTS voice options by language (100+ languages supported)
VOICES_BY_LANGUAGE = {
    # English variants
    'en': 'en-US-AriaNeural',
    'en-US': 'en-US-AriaNeural',
    'en-GB': 'en-GB-RyanNeural',
    'en-AU': 'en-AU-NatashaNeural',
    'en-CA': 'en-CA-ClaraNeural',
    'en-IN': 'en-IN-NeerjaNeural',
    'en-IE': 'en-IE-EmilyNeural',
    'en-NZ': 'en-NZ-MollyNeural',
    'en-SG': 'en-SG-LunaNeural',
    'en-ZA': 'en-ZA-LeahNeural',
    
    # Spanish variants
    'es': 'es-ES-AlvaroNeural',
    'es-ES': 'es-ES-AlvaroNeural',
    'es-MX': 'es-MX-DaliaNeural',
    'es-AR': 'es-AR-ElenaNeural',
    'es-CO': 'es-CO-SalomeNeural',
    'es-CL': 'es-CL-CatalinaNeural',
    
    # French variants
    'fr': 'fr-FR-DeniseNeural',
    'fr-FR': 'fr-FR-DeniseNeural',
    'fr-CA': 'fr-CA-SylvieNeural',
    'fr-BE': 'fr-BE-CharlineNeural',
    'fr-CH': 'fr-CH-ArianeNeural',
    
    # German variants
    'de': 'de-DE-ConradNeural',
    'de-DE': 'de-DE-ConradNeural',
    'de-AT': 'de-AT-IngridNeural',
    'de-CH': 'de-CH-LeniNeural',
    
    # Italian
    'it': 'it-IT-DiegoNeural',
    'it-IT': 'it-IT-DiegoNeural',
    
    # Portuguese variants
    'pt': 'pt-BR-FranciscaNeural',
    'pt-BR': 'pt-BR-FranciscaNeural',
    'pt-PT': 'pt-PT-DuarteNeural',
    
    # Japanese
    'ja': 'ja-JP-NanamiNeural',
    'ja-JP': 'ja-JP-NanamiNeural',
    
    # Chinese variants
    'zh': 'zh-CN-XiaoxiaoNeural',
    'zh-CN': 'zh-CN-XiaoxiaoNeural',
    'zh-TW': 'zh-TW-HsiaoChenNeural',
    'zh-HK': 'zh-HK-HiuGaaiNeural',
    
    # Korean
    'ko': 'ko-KR-SunHiNeural',
    'ko-KR': 'ko-KR-SunHiNeural',
    
    # Russian
    'ru': 'ru-RU-SvetlanaNeural',
    'ru-RU': 'ru-RU-SvetlanaNeural',
    
    # Arabic variants
    'ar': 'ar-SA-ZariyahNeural',
    'ar-SA': 'ar-SA-ZariyahNeural',
    'ar-AE': 'ar-AE-FatimaNeural',
    'ar-EG': 'ar-EG-SalmaNeural',
    
    # Hindi
    'hi': 'hi-IN-SwaraNeural',
    'hi-IN': 'hi-IN-SwaraNeural',
    
    # Thai
    'th': 'th-TH-PremwadeeNeural',
    'th-TH': 'th-TH-PremwadeeNeural',
    
    # Vietnamese
    'vi': 'vi-VN-HoaiMyNeural',
    'vi-VN': 'vi-VN-HoaiMyNeural',
    
    # Turkish
    'tr': 'tr-TR-EmelNeural',
    'tr-TR': 'tr-TR-EmelNeural',
    
    # Greek
    'el': 'el-GR-AthinaNeural',
    'el-GR': 'el-GR-AthinaNeural',
    
    # Dutch variants
    'nl': 'nl-NL-ColetteNeural',
    'nl-NL': 'nl-NL-ColetteNeural',
    'nl-BE': 'nl-BE-DenaNeural',
    
    # Polish
    'pl': 'pl-PL-ZofiaNeural',
    'pl-PL': 'pl-PL-ZofiaNeural',
    
    # Ukrainian
    'uk': 'uk-UA-PolinaNeural',
    'uk-UA': 'uk-UA-PolinaNeural',
    
    # Swedish
    'sv': 'sv-SE-SofieNeural',
    'sv-SE': 'sv-SE-SofieNeural',
    
    # Danish
    'da': 'da-DK-ChristelNeural',
    'da-DK': 'da-DK-ChristelNeural',
    
    # Finnish
    'fi': 'fi-FI-NooraNeural',
    'fi-FI': 'fi-FI-NooraNeural',
    
    # Norwegian
    'nb': 'nb-NO-PernilleNeural',
    'nb-NO': 'nb-NO-PernilleNeural',
    
    # Czech
    'cs': 'cs-CZ-VlastaNeural',
    'cs-CZ': 'cs-CZ-VlastaNeural',
    
    # Hungarian
    'hu': 'hu-HU-NoemiNeural',
    'hu-HU': 'hu-HU-NoemiNeural',
    
    # Romanian
    'ro': 'ro-RO-AlinaNeural',
    'ro-RO': 'ro-RO-AlinaNeural',
    
    # Slovak
    'sk': 'sk-SK-ViktoriaNeural',
    'sk-SK': 'sk-SK-ViktoriaNeural',
    
    # Hebrew
    'he': 'he-IL-HilaNeural',
    'he-IL': 'he-IL-HilaNeural',
    
    # Indonesian
    'id': 'id-ID-GadisNeural',
    'id-ID': 'id-ID-GadisNeural',
    
    # Malay
    'ms': 'ms-MY-YasminNeural',
    'ms-MY': 'ms-MY-YasminNeural',
    
    # Tagalog / Filipino
    'tl': 'fil-PH-BlessicaNeural',
    'fil': 'fil-PH-BlessicaNeural',
    'fil-PH': 'fil-PH-BlessicaNeural',
    
    # Afrikaans
    'af': 'af-ZA-AdriNeural',
    'af-ZA': 'af-ZA-AdriNeural',
    
    # Albanian
    'sq': 'sq-AL-AnilaNeural',
    'sq-AL': 'sq-AL-AnilaNeural',
    
    # Amharic
    'am': 'am-ET-MekdesNeural',
    'am-ET': 'am-ET-MekdesNeural',
    
    # Azerbaijani
    'az': 'az-AZ-BanuNeural',
    'az-AZ': 'az-AZ-BanuNeural',
    
    # Bengali
    'bn': 'bn-BD-NabanitaNeural',
    'bn-BD': 'bn-BD-NabanitaNeural',
    'bn-IN': 'bn-IN-TanishaaNeural',
    
    # Bosnian
    'bs': 'bs-BA-VesnaNeural',
    'bs-BA': 'bs-BA-VesnaNeural',
    
    # Bulgarian
    'bg': 'bg-BG-KalinaNeural',
    'bg-BG': 'bg-BG-KalinaNeural',
    
    # Burmese
    'my': 'my-MM-NilarNeural',
    'my-MM': 'my-MM-NilarNeural',
    
    # Catalan
    'ca': 'ca-ES-JoanaNeural',
    'ca-ES': 'ca-ES-JoanaNeural',
    
    # Croatian
    'hr': 'hr-HR-GabrijelaNeural',
    'hr-HR': 'hr-HR-GabrijelaNeural',
    
    # Estonian
    'et': 'et-EE-AnuNeural',
    'et-EE': 'et-EE-AnuNeural',
    
    # Galician
    'gl': 'gl-ES-SabelaNeural',
    'gl-ES': 'gl-ES-SabelaNeural',
    
    # Georgian
    'ka': 'ka-GE-EkaNeural',
    'ka-GE': 'ka-GE-EkaNeural',
    
    # Gujarati
    'gu': 'gu-IN-DhwaniNeural',
    'gu-IN': 'gu-IN-DhwaniNeural',
    
    # Irish
    'ga': 'ga-IE-OrlaNeural',
    'ga-IE': 'ga-IE-OrlaNeural',
    
    # Icelandic
    'is': 'is-IS-GudrunNeural',
    'is-IS': 'is-IS-GudrunNeural',
    
    # Javanese
    'jv': 'jv-ID-SitiNeural',
    'jv-ID': 'jv-ID-SitiNeural',
    
    # Kannada
    'kn': 'kn-IN-SapnaNeural',
    'kn-IN': 'kn-IN-SapnaNeural',
    
    # Kazakh
    'kk': 'kk-KZ-AigulNeural',
    'kk-KZ': 'kk-KZ-AigulNeural',
    
    # Khmer
    'km': 'km-KH-SreymomNeural',
    'km-KH': 'km-KH-SreymomNeural',
    
    # Lao
    'lo': 'lo-LA-KeomanyNeural',
    'lo-LA': 'lo-LA-KeomanyNeural',
    
    # Latvian
    'lv': 'lv-LV-EveritaNeural',
    'lv-LV': 'lv-LV-EveritaNeural',
    
    # Lithuanian
    'lt': 'lt-LT-OnaNeural',
    'lt-LT': 'lt-LT-OnaNeural',
    
    # Macedonian
    'mk': 'mk-MK-MarijaNeural',
    'mk-MK': 'mk-MK-MarijaNeural',
    
    # Malayalam
    'ml': 'ml-IN-SobhanaNeural',
    'ml-IN': 'ml-IN-SobhanaNeural',
    
    # Maltese
    'mt': 'mt-MT-GraceNeural',
    'mt-MT': 'mt-MT-GraceNeural',
    
    # Marathi
    'mr': 'mr-IN-AarohiNeural',
    'mr-IN': 'mr-IN-AarohiNeural',
    
    # Mongolian
    'mn': 'mn-MN-YesuiNeural',
    'mn-MN': 'mn-MN-YesuiNeural',
    
    # Nepali
    'ne': 'ne-NP-HemkalaNeural',
    'ne-NP': 'ne-NP-HemkalaNeural',
    
    # Pashto
    'ps': 'ps-AF-LatifaNeural',
    'ps-AF': 'ps-AF-LatifaNeural',
    
    # Persian/Farsi
    'fa': 'fa-IR-DilaraNeural',
    'fa-IR': 'fa-IR-DilaraNeural',
    
    # Serbian
    'sr': 'sr-RS-SophieNeural',
    'sr-RS': 'sr-RS-SophieNeural',
    
    # Sinhala
    'si': 'si-LK-ThiliniNeural',
    'si-LK': 'si-LK-ThiliniNeural',
    
    # Slovenian
    'sl': 'sl-SI-PetraNeural',
    'sl-SI': 'sl-SI-PetraNeural',
    
    # Somali
    'so': 'so-SO-UbaxNeural',
    'so-SO': 'so-SO-UbaxNeural',
    
    # Sundanese
    'su': 'su-ID-TutiNeural',
    'su-ID': 'su-ID-TutiNeural',
    
    # Swahili
    'sw': 'sw-KE-ZuriNeural',
    'sw-KE': 'sw-KE-ZuriNeural',
    'sw-TZ': 'sw-TZ-RehemaNeural',
    
    # Tamil
    'ta': 'ta-IN-PallaviNeural',
    'ta-IN': 'ta-IN-PallaviNeural',
    'ta-SG': 'ta-SG-VenbaNeural',
    'ta-LK': 'ta-LK-SaranyaNeural',
    'ta-MY': 'ta-MY-KaniNeural',
    
    # Telugu
    'te': 'te-IN-ShrutiNeural',
    'te-IN': 'te-IN-ShrutiNeural',
    
    # Urdu
    'ur': 'ur-IN-GulNeural',
    'ur-IN': 'ur-IN-GulNeural',
    'ur-PK': 'ur-PK-UzmaNeural',
    
    # Uzbek
    'uz': 'uz-UZ-MadinaNeural',
    'uz-UZ': 'uz-UZ-MadinaNeural',
    
    # Welsh
    'cy': 'cy-GB-NiaNeural',
    'cy-GB': 'cy-GB-NiaNeural',
    
    # Zulu
    'zu': 'zu-ZA-ThandoNeural',
    'zu-ZA': 'zu-ZA-ThandoNeural',
}


def detect_language(text: str) -> str:
    """Detect language from text and return language code."""
    # First, check for Japanese characters (hiragana & katakana)
    # Hiragana: U+3040 to U+309F
    # Katakana: U+30A0 to U+30FF
    has_hiragana = any('\u3040' <= char <= '\u309F' for char in text)
    has_katakana = any('\u30A0' <= char <= '\u30FF' for char in text)
    
    if has_hiragana or has_katakana:
        print(f"🔍 Detected Japanese characters in text")
        return 'ja'
    
    # Then, check for Chinese characters (CJK Unicode ranges)
    # Chinese characters are in ranges: 4E00-9FFF (CJK Unified Ideographs)
    # and F900-FAFF (CJK Compatibility Ideographs)
    has_chinese = any(
        '\u4E00' <= char <= '\u9FFF' or 
        '\uF900' <= char <= '\uFAFF'
        for char in text
    )
    if has_chinese:
        print(f"🔍 Detected Chinese characters in text")
        return 'zh'
    
    # Check for Traditional Chinese specific characters
    traditional_chinese_chars = set('譲謝貿購調話諸貴賣質賤資賦賢賡賦贅賺贅贊贈贏贓贔贖贗贙贝贞负')
    if any(char in traditional_chinese_chars for char in text):
        print(f"🔍 Detected Traditional Chinese characters")
        return 'zh-TW'
    
    # Check for Korean (Hangul)
    # Hangul Syllables: U+AC00 to U+D7AF
    has_korean = any('\uAC00' <= char <= '\uD7AF' for char in text)
    if has_korean:
        print(f"🔍 Detected Korean characters in text")
        return 'ko'
    
    # Then use langdetect for other languages
    try:
        from langdetect import detect, DetectorFactory
        # Ensure consistency
        DetectorFactory.seed = 0
        lang_code = detect(text)
        print(f"🔍 Detected language from text: {lang_code}")
        return lang_code
    except Exception as e:
        print(f"⚠️  Language detection from text failed: {e}")
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            lang_code = blob.detect_language()
            print(f"🔍 Detected language via TextBlob: {lang_code}")
            return lang_code
        except Exception as e2:
            print(f"⚠️  TextBlob detection also failed: {e2}")
            # Default to English if detection fails
            print("⚠️  Defaulting to English")
            return 'en'


def read_detected_language() -> str:
    """Read detected language from file (set by Stage 2)."""
    if os.path.exists(DETECTED_LANGUAGE_FILE):
        try:
            with open(DETECTED_LANGUAGE_FILE, 'r') as f:
                lang_code = f.read().strip()
                if lang_code:
                    return lang_code
        except:
            pass
    # Fallback to English
    return 'en'


def get_voice_for_language_code(lang_code: str) -> tuple[str, str]:
    """
    Get appropriate voice for the given language code.
    Language is pre-detected by Stage 2 for consistency and speed.
    
    Returns:
        (voice_id, language_name): Voice ID and language display name
    """
    # Normalize language code: handle lowercase variants
    # Convert zh-cn to zh-CN, zh-tw to zh-TW, etc.
    normalized_code = lang_code
    if lang_code.lower() == 'zh-cn':
        normalized_code = 'zh-CN'
    elif lang_code.lower() == 'zh-tw':
        normalized_code = 'zh-TW'
    elif lang_code.lower() == 'pt-br':
        normalized_code = 'pt-BR'
    elif lang_code.lower() == 'pt-pt':
        normalized_code = 'pt-PT'
    
    # Get voice for language code, fallback to English
    voice = VOICES_BY_LANGUAGE.get(normalized_code, VOICES_BY_LANGUAGE.get(lang_code, VOICES_BY_LANGUAGE['en']))
    
    # Language names for display
    lang_names = {
        # English
        'en': 'English', 'en-US': 'English (US)', 'en-GB': 'English (UK)', 
        'en-AU': 'English (Australia)', 'en-CA': 'English (Canada)', 
        'en-IN': 'English (India)', 'en-IE': 'English (Ireland)',
        'en-NZ': 'English (New Zealand)', 'en-SG': 'English (Singapore)',
        'en-ZA': 'English (South Africa)',
        
        # Spanish
        'es': 'Spanish', 'es-ES': 'Spanish (Spain)', 'es-MX': 'Spanish (Mexico)',
        'es-AR': 'Spanish (Argentina)', 'es-CO': 'Spanish (Colombia)',
        'es-CL': 'Spanish (Chile)',
        
        # French
        'fr': 'French', 'fr-FR': 'French (France)', 'fr-CA': 'French (Canada)',
        'fr-BE': 'French (Belgium)', 'fr-CH': 'French (Switzerland)',
        
        # German
        'de': 'German', 'de-DE': 'German (Germany)', 'de-AT': 'German (Austria)',
        'de-CH': 'German (Switzerland)',
        
        # Portuguese
        'pt': 'Portuguese', 'pt-BR': 'Portuguese (Brazil)', 'pt-PT': 'Portuguese (Portugal)',
        
        # Other major languages
        'it': 'Italian', 'it-IT': 'Italian',
        'ja': 'Japanese', 'ja-JP': 'Japanese',
        'zh': 'Chinese', 'zh-CN': 'Chinese (Simplified)', 'zh-TW': 'Chinese (Traditional)',
        'zh-HK': 'Chinese (Hong Kong)',
        'ko': 'Korean', 'ko-KR': 'Korean',
        'ru': 'Russian', 'ru-RU': 'Russian',
        'ar': 'Arabic', 'ar-SA': 'Arabic (Saudi Arabia)', 'ar-AE': 'Arabic (UAE)',
        'ar-EG': 'Arabic (Egypt)',
        'hi': 'Hindi', 'hi-IN': 'Hindi',
        'th': 'Thai', 'th-TH': 'Thai',
        'vi': 'Vietnamese', 'vi-VN': 'Vietnamese',
        'tr': 'Turkish', 'tr-TR': 'Turkish',
        'el': 'Greek', 'el-GR': 'Greek',
        'nl': 'Dutch', 'nl-NL': 'Dutch (Netherlands)', 'nl-BE': 'Dutch (Belgium)',
        'pl': 'Polish', 'pl-PL': 'Polish',
        'uk': 'Ukrainian', 'uk-UA': 'Ukrainian',
        'sv': 'Swedish', 'sv-SE': 'Swedish',
        'da': 'Danish', 'da-DK': 'Danish',
        'fi': 'Finnish', 'fi-FI': 'Finnish',
        'nb': 'Norwegian', 'nb-NO': 'Norwegian',
        'cs': 'Czech', 'cs-CZ': 'Czech',
        'hu': 'Hungarian', 'hu-HU': 'Hungarian',
        'ro': 'Romanian', 'ro-RO': 'Romanian',
        'sk': 'Slovak', 'sk-SK': 'Slovak',
        'he': 'Hebrew', 'he-IL': 'Hebrew',
        'id': 'Indonesian', 'id-ID': 'Indonesian',
        'ms': 'Malay', 'ms-MY': 'Malay',
        'tl': 'Tagalog', 'fil': 'Filipino', 'fil-PH': 'Filipino',
        
        # Additional languages
        'af': 'Afrikaans', 'af-ZA': 'Afrikaans',
        'sq': 'Albanian', 'sq-AL': 'Albanian',
        'am': 'Amharic', 'am-ET': 'Amharic',
        'az': 'Azerbaijani', 'az-AZ': 'Azerbaijani',
        'bn': 'Bengali', 'bn-BD': 'Bengali (Bangladesh)', 'bn-IN': 'Bengali (India)',
        'bs': 'Bosnian', 'bs-BA': 'Bosnian',
        'bg': 'Bulgarian', 'bg-BG': 'Bulgarian',
        'my': 'Burmese', 'my-MM': 'Burmese',
        'ca': 'Catalan', 'ca-ES': 'Catalan',
        'hr': 'Croatian', 'hr-HR': 'Croatian',
        'et': 'Estonian', 'et-EE': 'Estonian',
        'gl': 'Galician', 'gl-ES': 'Galician',
        'ka': 'Georgian', 'ka-GE': 'Georgian',
        'gu': 'Gujarati', 'gu-IN': 'Gujarati',
        'ga': 'Irish', 'ga-IE': 'Irish',
        'is': 'Icelandic', 'is-IS': 'Icelandic',
        'jv': 'Javanese', 'jv-ID': 'Javanese',
        'kn': 'Kannada', 'kn-IN': 'Kannada',
        'kk': 'Kazakh', 'kk-KZ': 'Kazakh',
        'km': 'Khmer', 'km-KH': 'Khmer',
        'lo': 'Lao', 'lo-LA': 'Lao',
        'lv': 'Latvian', 'lv-LV': 'Latvian',
        'lt': 'Lithuanian', 'lt-LT': 'Lithuanian',
        'mk': 'Macedonian', 'mk-MK': 'Macedonian',
        'ml': 'Malayalam', 'ml-IN': 'Malayalam',
        'mt': 'Maltese', 'mt-MT': 'Maltese',
        'mr': 'Marathi', 'mr-IN': 'Marathi',
        'mn': 'Mongolian', 'mn-MN': 'Mongolian',
        'ne': 'Nepali', 'ne-NP': 'Nepali',
        'ps': 'Pashto', 'ps-AF': 'Pashto',
        'fa': 'Persian', 'fa-IR': 'Persian',
        'sr': 'Serbian', 'sr-RS': 'Serbian',
        'si': 'Sinhala', 'si-LK': 'Sinhala',
        'sl': 'Slovenian', 'sl-SI': 'Slovenian',
        'so': 'Somali', 'so-SO': 'Somali',
        'su': 'Sundanese', 'su-ID': 'Sundanese',
        'sw': 'Swahili', 'sw-KE': 'Swahili (Kenya)', 'sw-TZ': 'Swahili (Tanzania)',
        'ta': 'Tamil', 'ta-IN': 'Tamil (India)', 'ta-SG': 'Tamil (Singapore)',
        'ta-LK': 'Tamil (Sri Lanka)', 'ta-MY': 'Tamil (Malaysia)',
        'te': 'Telugu', 'te-IN': 'Telugu',
        'ur': 'Urdu', 'ur-IN': 'Urdu (India)', 'ur-PK': 'Urdu (Pakistan)',
        'uz': 'Uzbek', 'uz-UZ': 'Uzbek',
        'cy': 'Welsh', 'cy-GB': 'Welsh',
        'zu': 'Zulu', 'zu-ZA': 'Zulu',
    }
    lang_name = lang_names.get(normalized_code, lang_names.get(lang_code, 'Unknown'))
    
    print(f"🌐 Using language: {lang_name} ({normalized_code}) → Voice: {voice}")
    return voice, lang_name


def wait_for_text(timeout=10, min_chars=10):
    """
    Wait for text in LLM response file with streaming support.
    Returns as soon as minimum chars available instead of waiting for complete response.
    """
    wait_start = time.time()
    start = time.time()
    last_size = 0
    stable_count = 0
    
    while (time.time() - start) < timeout:
        try:
            if os.path.exists(LLM_RESPONSE_FILE) and os.path.getsize(LLM_RESPONSE_FILE) > 0:
                current_size = os.path.getsize(LLM_RESPONSE_FILE)
                
                # Check if we have enough characters
                with open(LLM_RESPONSE_FILE, 'r') as f:
                    text = f.read().strip()
                    if len(text) >= min_chars:
                        # If file size hasn't changed for 2 checks, assume LLM is still writing
                        # Return partial text immediately for streaming synthesis
                        if current_size == last_size:
                            stable_count += 1
                            if stable_count >= 2:  # 2 checks = ~0.1s stable
                                wait_latency = time.time() - wait_start
                                print(f"⏱️  Streaming text available in {wait_latency:.2f}s: {len(text)} chars")
                                return text
                        else:
                            stable_count = 0
                        last_size = current_size
        except:
            pass
        time.sleep(0.05)  # Check every 50ms for responsiveness
    
    # Fallback: return whatever we have if timeout reached
    try:
        if os.path.exists(LLM_RESPONSE_FILE) and os.path.getsize(LLM_RESPONSE_FILE) > 0:
            with open(LLM_RESPONSE_FILE, 'r') as f:
                text = f.read().strip()
                if text:
                    print(f"⏱️  Timeout reached, synthesizing available text: {len(text)} chars")
                    return text
    except:
        pass
    
    return None


def play_audio(file_path):
    """Play audio file with threading for improved responsiveness."""
    try:
        from pydub import AudioSegment
        from pydub.playback import play
        import threading
        
        if os.path.exists(file_path):
            playback_start = time.time()
            audio = AudioSegment.from_file(file_path, format="mp3")
            
            # Calculate audio duration
            audio_duration = len(audio) / 1000.0  # Convert milliseconds to seconds
            
            print(f"🔊 Playing {audio_duration:.1f}s of audio...")
            
            # Play audio in background thread for responsiveness
            playback_complete = threading.Event()
            
            def play_in_thread():
                try:
                    play(audio)
                    playback_complete.set()
                except Exception as e:
                    print(f"⚠️  Playback error: {e}")
                    playback_complete.set()
            
            # Start playback in daemon thread
            playback_thread = threading.Thread(target=play_in_thread, daemon=True)
            playback_thread.start()
            
            # Wait for playback to complete with timeout
            # Timeout = audio duration + 1s buffer
            timeout = audio_duration + 1.0
            playback_complete.wait(timeout=timeout)
            
            playback_latency = time.time() - playback_start
            print(f"⏱️  Audio playback latency: {playback_latency:.2f}s")
            
            return True
    except Exception as e:
        print(f"Error playing audio: {e}")
    return False


async def generate_speech(text: str, voice: Optional[str] = None):
    """Generate speech using Edge TTS API (async) - optimized for low latency."""
    try:
        tts_start = time.time()
        print("🎙️  Streaming audio generation...")
        
        # If no voice provided, detect language from text
        if voice is None:
            # First try to read pre-detected language
            detected_lang = read_detected_language()
            
            # If we got English by default, try detecting from text
            if detected_lang == 'en':
                text_detected = detect_language(text)
                if text_detected and text_detected != 'en':
                    detected_lang = text_detected
            
            voice, lang_name = get_voice_for_language_code(detected_lang)
            print(f"⚡ Using language: {detected_lang}")
        
        # Remove any problematic characters from text
        text = text.strip()
        if not text:
            print("❌ Empty text provided for TTS")
            return None
        
        print(f"🗣️ Voice: {voice}, Text length: {len(text)} chars")
        
        # Generate speech using edge-tts with minimal retries (fail fast for speed)
        max_retries = 1  # Reduced from 2 for latency optimization
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(AUDIO_OUTPUT_FILE)
                
                # Check if file was created and has content
                if os.path.exists(AUDIO_OUTPUT_FILE):
                    file_size = os.path.getsize(AUDIO_OUTPUT_FILE)
                    if file_size > 0:
                        tts_latency = time.time() - tts_start
                        print(f"✓ Generated audio: {file_size} bytes")
                        print(f"⏱️  Total TTS latency: {tts_latency:.2f}s")
                        return AUDIO_OUTPUT_FILE
                    else:
                        print("❌ Audio file is empty, retrying...")
                        os.remove(AUDIO_OUTPUT_FILE)
                else:
                    print("❌ Audio file was not created, retrying...")
            except Exception as e:
                print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying...")
                    await asyncio.sleep(0.1)  # Reduced from 0.5 to 0.1 for speed
                else:
                    raise
        
        print("❌ Failed to generate audio after retries")
        return None
    
    except Exception as e:
        print(f"❌ Error generating speech: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Read LLM response and convert to speech using Edge TTS (concurrent-aware)."""
    
    stage4_start = time.time()
    
    # Wait for LLM response to be available (can start while LLM is still writing)
    text = wait_for_text(timeout=30)
    
    if not text:
        print("❌ No text received from LLM")
        sys.exit(1)
    
    print(f"📝 Text to synthesize ({len(text)} chars): {text[:50]}...")
    print("🔄 TTS: Generating speech with detected language...\n")
    
    # Generate speech - uses pre-detected language for speed
    audio_file = await generate_speech(text)
    
    if audio_file:
        print("🔊 Playing audio...")
        play_audio(audio_file)
        print("✅ Audio playback complete - microphone will start listening\n")
        
        stage4_latency = time.time() - stage4_start
        print(f"⏱️  Stage 4 (TTS) Total Latency: {stage4_latency:.2f}s\n")
        
        # Clean up
        try:
            os.remove(LLM_RESPONSE_FILE)
            os.remove(audio_file)
        except:
            pass
        
        sys.exit(0)
    else:
        print("❌ Failed to generate speech")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())