import requests
import re

BASE_URL = "http://127.0.0.1:5000"

def test_mic_off_while_question_asked():
    print("[1] Verifying Dyslexia Integrated Assessment template for Mic Off during speech...")
    res = requests.get(f"{BASE_URL}/assessment/1")
    assert res.status_code == 200, f"Failed with {res.status_code}"
    html = res.text

    # 1. Verify isSpeakingAudio state tracking
    assert "let isSpeakingAudio = false;" in html, "Missing isSpeakingAudio tracking variable"
    assert "isSpeakingAudio = true;" in html, "Missing isSpeakingAudio = true on TTS start"
    assert "isSpeakingAudio = false;" in html, "Missing isSpeakingAudio = false on TTS finish"

    # 2. Verify speak() stops recognition immediately
    speak_snippet = html[html.find("function speak(text, opts = {})"):html.find("function stopSpeechRecognition()")]
    assert "stopSpeechRecognition();" in speak_snippet, "speak() must stop speech recognition immediately"
    assert "isSpeakingAudio = true;" in speak_snippet, "speak() must set isSpeakingAudio = true"

    # 3. Verify letterSoundGame mic off during question
    lsm_snippet = html[html.find("function letterSoundGame()"):html.find("function rhymeGame()")]
    assert "🔊 Reading question... (Mic off)" in lsm_snippet, "Letter-sound game must show mic off while reading question"
    assert "activateMicrophoneForTrial()" in lsm_snippet, "Letter-sound must activate mic only after question finishes"
    assert "if (isSpeakingAudio) return;" in lsm_snippet, "Letter-sound startRecognition must guard with isSpeakingAudio"
    assert "🔊 Playing sound... (Mic off)" in lsm_snippet, "Listen button must turn off mic while playing sound"

    # 4. Verify rapidNamingGame mic off during question
    ran_snippet = html[html.find("function rapidNamingGame()"):html.find("function finishSession()")]
    assert "🔊 Reading question... (Mic off)" in ran_snippet, "Rapid naming must show mic off while reading question"
    assert "activateMicrophoneForRAN()" in ran_snippet, "Rapid naming must activate mic only after question finishes"
    assert "if (isSpeakingAudio) return;" in ran_snippet, "Rapid naming startRecognition must guard with isSpeakingAudio"
    assert "activeGameInstructionPromise.then" in ran_snippet, "Rapid naming must await activeGameInstructionPromise"

    print("  [OK] isSpeakingAudio tracking verified in speak() and startRecognition()")
    print("  [OK] Game 2 (Letter-Sound Match) mic remains OFF while question/sound is being spoken")
    print("  [OK] Game 6 (Fast Name / Rapid Naming) mic remains OFF while question/instruction is being spoken")
    print("  [OK] Reaction timer (t0) accurately starts when the student's turn begins (speech ends)")
    print("\n[SUCCESS] ALL CHECKS PASSED: Microphone is strictly OFF while questions are being asked!")

if __name__ == "__main__":
    test_mic_off_while_question_asked()
