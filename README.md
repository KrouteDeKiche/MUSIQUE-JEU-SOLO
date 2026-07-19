# 🦀 Auto_Spotify : L'IA qui gère ta musique en jeu

[![en](https://img.shields.io/badge/lang-en-red.svg)](README_en.md)

Auto_Spotify est un script Python intelligent qui écoute le son de tes jeux vidéo. Dès qu'il entend de l'action (tirs, musique in-game, cinématiques), il coupe automatiquement Chrome/Spotify. Quand le silence revient, ta musique repart toute seule !

---

## 🛠️ Partie 1 : Installation et Prérequis

Pour que l'IA puisse tourner sur ta machine, il te faut un environnement Python fonctionnel et quelques bibliothèques.

1. Installe **Python 3.9 ou supérieur** sur ton ordinateur.
2. Ouvre ton terminal (ou invite de commande) dans le dossier du projet.
3. Mets à jour ton gestionnaire de paquets pour éviter les erreurs d'installation :
   * **Sur Windows :** `python -m pip install --upgrade pip`
   * **Sur Linux :** `sudo apt update && sudo apt install python3-pip`
4. Installe toutes les dépendances nécessaires en tapant cette commande :
   `pip install tensorflow tensorflow-hub numpy sounddevice keyboard pycaw comtypes`
5. **Au tout premier lancement du script**, l'intelligence artificielle (le modèle YAMNet de Google) va se télécharger automatiquement dans un dossier `cerveau_ia`. Cela prend quelques secondes et nécessite une connexion internet. Les lancements suivants seront instantanés !

---

## 🎧 Partie 2 : Le Câble Virtuel (Configuration Audio)

**⚠️ Étape cruciale !** Si tu ne fais pas ça, l'IA va écouter Spotify, croire que c'est le jeu, couper Spotify, entendre du silence, rallumer Spotify... et créer une boucle infinie infernale. Il faut isoler le son du jeu grâce à un câble virtuel.

### 🪟 Pour les utilisateurs Windows

**1. Télécharger VB-Audio Virtual Cable**
1. Rends-toi sur le site officiel : [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
2. Télécharge la version gratuite pour Windows et installe-la (un redémarrage du PC est souvent conseillé).

**2. Router le son du jeu**
1. Ouvre les paramètres de son de Windows > **Mélangeur de volume** (ou "Options d'ergonomie audio").
2. Cherche ton jeu vidéo dans la liste des applications ouvertes.
3. Change sa sortie audio (Output) pour la mettre sur **CABLE Input (VB-Audio Virtual Cable)**.

**3. Entendre ton jeu (Routage du Câble vers ton Casque)**
Puisque ton jeu envoie maintenant son son dans un câble virtuel, tu n'entendras plus rien dans ton casque. Pour régler ça, il faut dire à Windows de rediriger le son du câble vers tes oreilles :
1. Appuie sur les touches **Windows + R** de ton clavier pour ouvrir la fenêtre "Exécuter".
2. Tape exactement `mmsys.cpl` et appuie sur **Entrée**. *(Cela ouvre instantanément la fenêtre classique "Son" de Windows)*.
3. En haut de cette fenêtre, clique sur le deuxième onglet : **Enregistrement**.
4. Cherche la ligne **CABLE Output (VB-Audio Virtual Cable)**, fais un clic droit dessus et choisis **Propriétés**.
5. Ouvre l'onglet **Écouter**.
6. Coche la case **"Écouter ce périphérique"**.
7. Dans le menu déroulant juste en dessous ("Lire ce périphérique via"), **sélectionne ton vrai casque ou tes écouteurs principaux**.
8. Clique sur **Appliquer** puis sur **OK**.

### 🐧 Pour les utilisateurs Linux (PulseAudio / PipeWire)
Sur Linux, pas besoin de logiciel tiers !
1. Ouvre un terminal et crée un câble virtuel avec cette commande :
   `pactl load-module module-null-sink sink_name=VirtualCable sink_properties=device.description="Virtual_Cable"`
2. Installe et ouvre le contrôleur de volume : `sudo apt install pavucontrol && pavucontrol`
3. Dans l'onglet **Lecture** (Playback), trouve ton jeu et redirige sa sortie vers **Virtual_Cable**.
4. L'IA devra écouter le "Monitor of Virtual_Cable".

### 🚀 Lancer le script
1. Lance le fichier `auto_spotify.py`.
2. Le script va scanner tes périphériques et te demander d'entrer un numéro.
3. Cherche dans la liste la ligne nommée exactement **CABLE Output (VB-Audio Virtual Cable)** *(Il y en a plusieurs, il faut choisir celui avec le plus grand chiffre. Dans mon cas, c'est le 24)*. 
4. Ce choix sera mémorisé pour les prochaines fois. S'il y a un bug lors des prochains lancements, c'est sûrement de là que ça vient : il te suffira de supprimer le fichier `config_audio.txt`. Bon jeu !

---

## 🧠 Partie 3 : Toutes les fonctionnalités (Comment ça marche ?)

Ce programme ne se contente pas d'appuyer sur "Play/Pause" bêtement. Il intègre plusieurs mécaniques avancées pour rendre ton expérience de jeu la plus fluide et agréable possible. Voici tout ce qu'il se passe sous le capot :

### 🕵️ 1. L'Écoute intelligente et le mode "Éco" (Anti-Surcharge)
* **Analyse en temps réel :** L'IA (basée sur le modèle YAMNet) écoute des extraits audio d'environ une seconde (0.975s) en boucle. Elle classe les sons entendus et vérifie si la catégorie "Music" arrive en tête de ses certitudes.
* **Bouclier Anti-Vide :** Si ton jeu est totalement silencieux (aucun son n'est envoyé dans le câble virtuel), le script le détecte instantanément. Au lieu de forcer le réseau de neurones à analyser du vide absolu (ce qui consommerait ton processeur pour rien), il court-circuite l'IA jusqu'au prochain bruit !

### 🎚️ 2. Le Contrôle du Volume (Fade In & Fade Out)
C'est la fonctionnalité phare pour le confort de tes oreilles. Le script ne coupe pas la musique brutalement, il agit comme un vrai DJ :
* **Ciblage chirurgical :** Le programme s'infiltre dans le mélangeur de volume de Windows pour y trouver spécifiquement `chrome.exe` (là où tourne ton Spotify Web ou YouTube). Il mémorise son volume de départ.
* **↘️ Fade Out (1.5 seconde) :** Quand l'IA entend une musique dans ton jeu, le script baisse progressivement le volume de Chrome jusqu'à 0 en 1.5 seconde. La transition est douce. Une fois le silence fait, il simule l'appui sur la touche multimédia "Pause" de ton clavier.
* **↗️ Fade In (5.0 secondes) :** Quand l'action se calme, le script appuie sur "Play", puis remonte le volume de Chrome très lentement sur 5 secondes. Ton retour à ta musique perso se fait sans aucune agression auditive.

### ⏳ 3. La jauge de "Patience" (7.5 secondes)
Pour éviter que ton Spotify s'allume et se coupe de manière intempestive au moindre dialogue de PNJ ou petit blanc musical dans ton jeu, le script possède une jauge de patience. 
* Après avoir coupé Spotify, il attendra un **silence musical in-game ininterrompu de 7.5 secondes** avant de décider qu'il est temps de relancer ta musique.

### 💾 4. La Mémoire du matériel
* Au premier lancement, tu choisis le numéro de ton périphérique audio (Virtual Cable). Le programme crée un fichier local `config_audio.txt` pour sauvegarder ce choix. 
* Aux lancements suivants, il démarre de manière 100% autonome. *Bonus : si ton câble virtuel change de numéro à cause d'une mise à jour Windows, le script le remarquera, bloquera l'erreur, et te rouvrira le menu de sélection automatiquement.*

### 🛑 5. L'Arrêt d'urgence propre (Safe Exit)
* Tu as fini de jouer ? Appuie simplement sur `Ctrl + C` dans le terminal.
* Le script capte cette commande d'arrêt, interrompt l'écoute, et surtout : **restaure immédiatement le volume de Chrome à son état normal**. Tu ne te retrouveras jamais avec un navigateur définitivement muet à cause du programme !

---

## ⚙️ Partie 4 : Personnalisation des réglages

Si tu trouves que l'IA est trop sensible ou que les transitions sont trop lentes, tu peux ouvrir `auto_spotify.py` avec ton éditeur de code et modifier les variables de configuration tout en haut du fichier :

*   `PATIENCE_TIME = 7.5` : Le temps (en secondes) que le script attend avant de relancer Spotify après la fin d'un son de jeu.
*   `FADE_OUT_TIME = 1.5` : La vitesse (en secondes) à laquelle le volume de Chrome descend.
*   `FADE_IN_TIME = 5.0` : La vitesse (en secondes) à laquelle le volume de Chrome remonte.

---

## 🆘 Partie 5 : Support et Dépannage

Si tu rencontres un problème en utilisant Auto_Spotify, voici les solutions aux soucis les plus courants.

*   **Le script affiche `ModuleNotFoundError` au lancement :** 
    Tu as oublié d'installer les dépendances. Relance la commande `pip install ...` fournie dans la Partie 1 dans ton terminal.
*   **Le volume de Chrome baisse mais la musique ne s'arrête pas :** 
    Vérifie que tu utilises bien le navigateur Google Chrome officiel et que tu n'as pas désactivé ou réassigné la touche multimédia "Play/Pause" de ton clavier.
*   **L'IA s'emmêle les pinceaux et tourne en boucle (ou n'entend que du "White Noise") :** 
    Le mauvais câble est écouté. Supprime le petit fichier `config_audio.txt` qui s'est créé dans ton dossier, puis relance le script pour choisir à nouveau le bon périphérique (le numéro WASAPI le plus élevé correspondant à `CABLE Output`).

---

## 📝 Licence & Crédits

*   **Développeur :** [Giovanni Kuntz](https://github.com/KrouteDeKiche)
*   **Cerveau IA :** Propulsé par le modèle audio Google YAMNet (via TensorFlow Hub).
*   **Licence :** Fais ce que tu veux de ce code !