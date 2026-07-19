import os
import sys
import time
import threading
import logging 
import warnings 

# 1. On coupe le sifflet au moteur C++ de TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- LE CHRONOMÈTRE EN ARRIÈRE-PLAN ---
chargement_en_cours = True
debut_chrono = time.time()

def afficher_chrono():
    while chargement_en_cours:
        temps_ecoule = round(time.time() - debut_chrono, 1)
        sys.stdout.write(f"\r⏳ Échauffement de l'IA en cours... {temps_ecoule}s")
        sys.stdout.flush()
        time.sleep(0.1)

fil_chrono = threading.Thread(target=afficher_chrono)
fil_chrono.start()
# --------------------------------------

# 2. On coupe le sifflet aux alertes Python (pour cacher le texte rouge)
logging.getLogger('tensorflow').setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# --- IMPORTS LOURDS (C'est ça qui prend 13 secondes) ---
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import sounddevice as sd
import keyboard
import csv
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume 
from comtypes import GUID, IUnknown, COMMETHOD, POINTER
from ctypes import c_float, HRESULT

# --- LE STÉTHOSCOPE POUR CHROME ---
class IAudioMeterInformation(IUnknown):
    _iid_ = GUID('{C02216F6-8C67-4B5B-9D00-D008E73E0064}')
    _methods_ = [
        COMMETHOD([], HRESULT, 'GetPeakValue', (['out'], POINTER(c_float), 'pfPeak'))
    ]

# --- CONFIGURATION ---
DEVICE_ID = 27  
FS_IA = 16000   
DURATION = 0.975 
PATIENCE_TIME = 7.5 

FADE_OUT_TIME = 1.5  
FADE_IN_TIME = 5.0   
# ---------------------

# --- CHARGEMENT ABSOLU (0% Internet, 100% Disque Dur) ---
chemin_cerveau = r"D:\kuntz\Documents\Projet_code\Auto_spotify\cerveau_ia\9616fd04ec2360621642ef9455b84f4b668e219e"

# On charge le modèle (C'est ça qui prend les 7 dernières secondes)
model = hub.load(chemin_cerveau)

# On extrait le vocabulaire de l'IA
class_map_path = model.class_map_path().numpy().decode('utf-8')
class_names = []
with open(class_map_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader) 
    for row in reader:
        class_names.append(row[2])
# --------------------------------------------------------

# On arrête le chrono une fois que tout est chargé
chargement_en_cours = False
fil_chrono.join()
temps_total = round(time.time() - debut_chrono, 1)

# On saute une ligne pour ne pas écraser le chrono final
print(f"\n🦀 L'IA est prête ! (Temps total de chauffe : {temps_total} secondes)")
print("MODE DEBUG COMPLET ACTIVÉ.\n")

def get_spotify_volume_control():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name().lower() == "chrome.exe":
            return session._ctl.QueryInterface(ISimpleAudioVolume)
    return None

def is_chrome_playing_audio():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name().lower() == "chrome.exe":
            try:
                meter = session._ctl.QueryInterface(IAudioMeterInformation)
                for _ in range(5):
                    if meter.GetPeakValue() > 0.0001:
                        return True
                    time.sleep(0.02)
            except Exception:
                pass
    return False

def smooth_fade(spotify_ctrl, start_vol, end_vol, duration):
    if not spotify_ctrl: return
    steps = 20 
    sleep_time = duration / steps
    vol_step = (end_vol - start_vol) / steps
    
    current_vol = start_vol
    for i in range(steps):
        current_vol += vol_step
        current_vol = max(0.0, min(1.0, current_vol))
        try:
            spotify_ctrl.SetMasterVolume(current_vol, None)
        except:
            break
        time.sleep(sleep_time)
        
    spotify_ctrl.SetMasterVolume(end_vol, None)

def is_it_music(audio_data):
    scores, embeddings, spectrogram = model(audio_data)
    mean_scores = np.mean(scores, axis=0)
    top_3_indices = np.argsort(mean_scores)[::-1][:3]
    top_3_classes = [class_names[i] for i in top_3_indices]
    top_3_scores = [mean_scores[i] for i in top_3_indices]
    top_prediction = top_3_classes[0]
    return "Music" in top_prediction, top_3_classes, top_3_scores

def main():
    # --- RÉGLAGE INITIAL DU VOLUME ---
    # On va chercher le volume actuel de Chrome dès le lancement
    initial_ctrl = get_spotify_volume_control()
    if initial_ctrl:
        normal_spotify_volume = initial_ctrl.GetMasterVolume()
        print(f"🔈 Volume Chrome actuel détecté : {int(normal_spotify_volume * 100)}%.")
    else:
        normal_spotify_volume = 1.0
        print("🔈 Chrome non détecté au lancement, volume par défaut réglé à 100%.")
    # ----------------------------------

    print("🦀 L'IA est prête ! (Temps total de chauffe : ...)")
    
    is_paused = False           
    script_paused_chrome = False 
    silence_start_time = None

    try:
        device_info = sd.query_devices(DEVICE_ID, 'input')
        native_fs = int(device_info['default_samplerate'])
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        return

    try:
        while True:
            try:
                audio_capture = sd.rec(int(DURATION * native_fs), samplerate=native_fs, channels=2, dtype='float32', device=DEVICE_ID)
                sd.wait()
                
                audio_mono = np.mean(audio_capture, axis=1)
                step = max(1, int(native_fs / FS_IA))
                audio_data = audio_mono[::step]

                is_music, top_3_classes, top_3_scores = is_it_music(audio_data)
                print(f"🎧 J'entends : 1.{top_3_classes[0]} ({int(top_3_scores[0]*100)}%) | 2.{top_3_classes[1]} ({int(top_3_scores[1]*100)}%)")

                if is_music:
                    silence_start_time = None 
                    
                    if not is_paused:
                        if is_chrome_playing_audio():
                            print(f"↘️ Musique de jeu détectée ! Chrome fait du bruit, je le coupe.")
                            ctrl = get_spotify_volume_control()
                            if ctrl:
                                normal_spotify_volume = ctrl.GetMasterVolume()
                                smooth_fade(ctrl, normal_spotify_volume, 0.0, FADE_OUT_TIME)
                            
                            keyboard.send("play/pause media")
                            script_paused_chrome = True 
                        else:
                            print(f"🤫 Musique de jeu détectée, mais Chrome est silencieux. Je ne touche à rien !")
                            script_paused_chrome = False
                            
                        is_paused = True 
                
                else:
                    if is_paused:
                        if silence_start_time is None:
                            silence_start_time = time.time()
                            print(f"⏳ La musique semble s'arrêter... J'attends {PATIENCE_TIME} secondes.")
                            
                        elif time.time() - silence_start_time >= PATIENCE_TIME:
                            if script_paused_chrome:
                                print(f"↗️ Silence confirmé. Je rallume Chrome.")
                                keyboard.send("play/pause media")
                                
                                ctrl = None
                                for _ in range(15):
                                    ctrl = get_spotify_volume_control()
                                    if ctrl:
                                        break
                                    time.sleep(0.2)
                                
                                if ctrl:
                                    smooth_fade(ctrl, 0.0, normal_spotify_volume, FADE_IN_TIME)
                                else:
                                    print("⚠️ Impossible de retrouver Chrome dans le mélangeur !")
                            else:
                                print("🔄 Silence de retour. Je réinitialise (ce n'est pas moi qui avais coupé).")
                                
                            is_paused = False 
                            script_paused_chrome = False 
                            silence_start_time = None 
            
            except Exception as e:
                print(f"Oups, erreur pendant l'écoute : {e}")
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n🦀 [ARRÊT] Ctrl+C détecté ! Rangement des pinces en cours...")
        time.sleep(0.5)
        ctrl = get_spotify_volume_control()
        if ctrl:
            print("🔊 Restauration du volume de Chrome à la normale...")
            ctrl.SetMasterVolume(normal_spotify_volume, None)
        print("🛑 Programme terminé proprement. Ta musique reste dans son état actuel !")

if __name__ == "__main__":
    main()