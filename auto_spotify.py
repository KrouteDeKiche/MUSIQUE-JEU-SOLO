import os
import sys
import time
import threading
import logging 
import warnings 

# 1. On coupe le sifflet au moteur C++ de TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- CONFIGURATION DU CACHE ---
# On force TensorFlow à sauvegarder le modèle dans un dossier local (cerveau_ia) juste à côté du script
dossier_local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cerveau_ia")
os.environ["TFHUB_CACHE_DIR"] = dossier_local

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
fil_chrono.daemon = True  # <- SÉCURITÉ ANTI-ZOMBIE : Le chrono meurt si le programme plante
fil_chrono.start()
# --------------------------------------

# 2. On coupe le sifflet aux alertes Python (pour cacher le texte rouge)
logging.getLogger('tensorflow').setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

# --- IMPORTS LOURDS SÉCURISÉS ---
try:
    import tensorflow as tf
    import tensorflow_hub as hub
    import numpy as np
    import sounddevice as sd
    import keyboard
    import csv
    from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume 
    from comtypes import GUID, IUnknown, COMMETHOD, POINTER
    from ctypes import c_float, HRESULT
except ImportError as e:
    chargement_en_cours = False
    print(f"\n\n❌ Oups ! Il manque un module pour faire tourner le programme : {e}")
    print("👉 Tape cette commande dans ton terminal pour tout installer :")
    print("pip install tensorflow tensorflow-hub numpy sounddevice keyboard pycaw comtypes\n")
    sys.exit(1)

# --- LE STÉTHOSCOPE POUR CHROME ---
class IAudioMeterInformation(IUnknown):
    _iid_ = GUID('{C02216F6-8C67-4B5B-9D00-D008E73E0064}')
    _methods_ = [
        COMMETHOD([], HRESULT, 'GetPeakValue', (['out'], POINTER(c_float), 'pfPeak'))
    ]

# --- CONFIGURATION ---
FS_IA = 16000   
DURATION = 0.975 
PATIENCE_TIME = 7.5 

FADE_OUT_TIME = 1.5  
FADE_IN_TIME = 5.0   

# Fichier de sauvegarde pour le périphérique audio
fichier_config_audio = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_audio.txt")
# ---------------------

# --- CHARGEMENT DYNAMIQUE (Télécharge au 1er lancement, puis lit depuis le disque) ---
chemin_cerveau = "https://tfhub.dev/google/yamnet/1"

# On charge le modèle
try:
    model = hub.load(chemin_cerveau)
except Exception as e:
    chargement_en_cours = False
    print(f"\n\n❌ Impossible de télécharger ou charger le modèle IA : {e}")
    print("Vérifie ta connexion internet pour le premier lancement !")
    sys.exit(1)

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
    DEVICE_ID = None
    
    # --- TENTATIVE DE LECTURE DE LA SAUVEGARDE ---
    if os.path.exists(fichier_config_audio):
        try:
            with open(fichier_config_audio, 'r') as f:
                saved_id = int(f.read().strip())
            # On vérifie que ce périphérique existe toujours et fonctionne
            sd.query_devices(saved_id, 'input')
            DEVICE_ID = saved_id
            print(f"✅ Périphérique audio chargé depuis la sauvegarde (ID: {DEVICE_ID})")
        except Exception:
            print("⚠️ Le périphérique sauvegardé n'est plus valide ou introuvable. Nouvelle sélection requise.")
            DEVICE_ID = None

    # --- SÉLECTION DU PÉRIPHÉRIQUE INTERACTIVE (Si pas de sauvegarde ou erreur) ---
    if DEVICE_ID is None:
        print("🔍 SÉLECTION DU PÉRIPHÉRIQUE AUDIO")
        print("Voici la liste des microphones et sorties virtuelles de ton PC :")
        try:
            devices = sd.query_devices()
            for i, dev in enumerate(devices):
                # On affiche uniquement ceux capables de capturer du son
                if dev['max_input_channels'] > 0:
                    print(f"   [{i}] {dev['name']}")
            
            while True:
                try:
                    choix = input("\n👉 Tape le numéro du périphérique à écouter (cherche 'Mixage Stéréo' ou 'Virtual Cable') : ")
                    DEVICE_ID = int(choix)
                    # On vérifie que le numéro est valide
                    sd.query_devices(DEVICE_ID, 'input')
                    
                    # On sauvegarde le choix pour la prochaine fois
                    with open(fichier_config_audio, 'w') as f:
                        f.write(str(DEVICE_ID))
                        
                    print("✅ Périphérique validé et sauvegardé pour tes prochains lancements !\n")
                    break
                except Exception:
                    print("❌ Numéro invalide ou incompatible, réessaie.")
        except Exception as e:
            print(f"❌ Impossible de lister les périphériques : {e}")
            return

    # --- RÉGLAGE INITIAL DU VOLUME ---
    initial_ctrl = get_spotify_volume_control()
    if initial_ctrl:
        normal_spotify_volume = initial_ctrl.GetMasterVolume()
        print(f"🔈 Volume Chrome actuel détecté : {int(normal_spotify_volume * 100)}%.")
    else:
        normal_spotify_volume = 1.0
        print("🔈 Chrome non détecté au lancement, volume par défaut réglé à 100%.")
    # ----------------------------------
    
    is_paused = False           
    script_paused_chrome = False 
    silence_start_time = None

    try:
        device_info = sd.query_devices(DEVICE_ID, 'input')
        native_fs = int(device_info['default_samplerate'])
        print(f"🎤 Écoute en cours sur : {device_info['name']}")
    except Exception as e:
        print(f"❌ Erreur critique avec le périphérique audio : {e}")
        return

    try:
        while True:
            try:
                audio_capture = sd.rec(int(DURATION * native_fs), samplerate=native_fs, channels=2, dtype='float32', device=DEVICE_ID)
                sd.wait()
                
                audio_mono = np.mean(audio_capture, axis=1)
                step = max(1, int(native_fs / FS_IA))
                audio_data = audio_mono[::step]

                # --- NOUVELLE SÉCURITÉ ANTI-AVC POUR L'IA ---
                # 1. On nettoie les bugs du câble virtuel (remplace les NaN par des zéros)
                audio_data = np.nan_to_num(audio_data)
                
                # 2. Si le câble n'envoie aucun son, on évite de solliciter l'IA
                if np.max(np.abs(audio_data)) < 1e-4:
                    is_music = False
                    top_3_classes = ["Silence Absolu", "Rien", "Rien"]
                    top_3_scores = [1.0, 0.0, 0.0]
                else:
                    is_music, top_3_classes, top_3_scores = is_it_music(audio_data)
                # ---------------------------------------------

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