
import json
import os
import time
from openai import OpenAI


API_KEY = "" 

# Dossiers
INPUT_DIR = "./jsonlist"
OUTPUT_DIR = "./jsonlistWithData"
FINAL_MERGED_FILE = "BIBLIOTHEQUE_COMPLETE_TRIEE.json"

# Modèle
MODEL = "gpt-4o" 
SYSTEM_PROMPT = """
Tu es un Expert Musical et un DJ professionnel résident dans les plus grands clubs. Ta mission est de classer des fichiers musicaux pour une bibliothèque DJ (Serato) avec une précision extrême.

RÈGLES DE TRI (LOGIQUE DJ) :

1.  **LOGIQUE DE GENRE (La Racine) :**
    Choisis UN seul genre principal parmi cette liste stricte :
    - **URBAN** (Hip-hop actuel, Rap US/FR, RnB, Drill, Trap, Afro-Urban).
    - **SHATTA_BOUYON** (Shatta, Bouyon, Dancehall rapide style Antilles/Réunion/Guyane).
    - **ELECTRONIC** (House, Tech House, EDM, Trance).
    - **OPEN_FORMAT** (Pop, Variété, Hits Radio, Rock, Latino Pop commercial).
    - **LATINO** (Reggaeton, Moombahton, Baile Funk, Perreo - hors Pop commerciale).
    - **DISCO_FUNK** (Disco, Funk, Soul, Nu-Disco).
    - **OLDIES** (Années 80, 90, Rock classique).
    
    ⚠️ **EXCEPTION IMPORTANTE (JURISPRUDENCE CLUB) :** Si le titre date des années 2000-2010 mais qu'il est encore joué couramment en club comme un "Banger" actuel (ex: Flo Rida "Low", 50 Cent "In Da Club", Usher "Yeah", David Guetta), CLASSE-LE DANS **"URBAN"** ou **"OPEN_FORMAT"**, et surtout PAS dans OLDIES. Garde OLDIES pour les sons qui sonnent vraiment "rétro/nostalgie" (ex: Dr. Dre, Gala, Indochine).

2.  **LOGIQUE DE SOUS-GENRE :**
    Sois précis (ex: "Drill FR", "Zouk", "French Touch", "Jersey Club").

3.  **RÈGLE D'OR DE L'ÉNERGIE (Level 1-5) - L'IMPACT DANCEFLOOR :**
    Ne juge pas l'énergie seulement sur le BPM. Juge la **réaction du public**.
    - **Level 5 (Peak Time/Banger) :** Un morceau qui fait crier et courir les gens sur la piste. 
      *ATTENTION :* Un hit viral (ex: Jungeli "Petit Génie", Heuss "Moulaga") est une Énergie 5, même si le tempo est lent. L'impact culturel prime sur la vitesse.
    - **Level 3 (Groove) :** Ça danse, c'est fluide, mais pas d'explosion.
    - **Level 1 (Chill) :** Musique d'ambiance ou Warm-up très calme.

RÈGLES TECHNIQUES (FORMAT JSON) :

1.  **PAS DE RÉSUMÉ :** Tu dois traiter CHAQUE titre de la liste un par un. Ne fais jamais de synthèse.
2.  **STRUCTURE OBLIGATOIRE :**
    Tu dois retourner un objet JSON contenant une seule clé "tracks".
    Cette clé contient la liste des objets.

Exemple de sortie attendue :
{
  "tracks": [
    {
      "filename": "Nom exact du fichier reçu (NE PAS MODIFIER)",
      "artist": "Nom corrigé",
      "title": "Titre corrigé",
      "main_genre": "GENRE_PRINCIPAL",
      "sub_genre": "Sous-genre précis",
      "energy_level": 5,
      "vibe_tags": ["Viral", "Hit", "Club"]
    }
  ]
}
"""
# =================================================

def process_and_merge():
    client = OpenAI(api_key=API_KEY)

    # Création du dossier de sortie si inexistant
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # --- PHASE 1 : TRAITEMENT INDIVIDUEL ---
    
    try:
        input_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    except FileNotFoundError:
        print(f"❌ Erreur : Le dossier '{INPUT_DIR}' n'existe pas. Crée-le et mets tes json dedans.")
        return

    total_files = len(input_files)
    print(f"📦 {total_files} fichiers trouvés dans '{INPUT_DIR}' à traiter.")

    for index, filename in enumerate(input_files):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)

        # Vérifier si le fichier a déjà été traité
        if os.path.exists(output_path):
            print(f"⏩ Fichier {index+1}/{total_files} déjà traité : {filename}")
            continue

        print(f"🤖 Traitement IA {index+1}/{total_files} : {filename} ...")

        try:
            # Lecture du petit fichier
            with open(input_path, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)

            # Envoi à l'IA
            user_content = json.dumps(batch_data, ensure_ascii=False)
            
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyse cette liste de fichiers audio : {user_content}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.0, 
            )

            # Parsing de la réponse
            content = response.choices[0].message.content
            ai_data = json.loads(content)

            # Gestion du format de réponse
            final_data = []
            if isinstance(ai_data, list):
                final_data = ai_data
            elif isinstance(ai_data, dict):
                for val in ai_data.values():
                    if isinstance(val, list):
                        final_data = val
                        break
            
            # Sauvegarde du résultat individuel
            if final_data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, indent=4, ensure_ascii=False)
            else:
                print(f"⚠️ Attention : Résultat vide pour {filename}")

            time.sleep(0.5) 

        except Exception as e:
            print(f"❌ ERREUR sur {filename} : {e}")
            continue

    print("\n✅ PHASE 1 TERMINÉE : Tous les fichiers sont traités.")
    print("-" * 40)

    # --- PHASE 2 : FUSION (MERGE) ---
    print("🔄 Démarrage de la fusion des fichiers...")

    all_tracks = []
    processed_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json')]

    for filename in processed_files:
        file_path = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_tracks.extend(data)
                else:
                    print(f"⚠️ Format ignoré dans {filename} (pas une liste)")
        except Exception as e:
            print(f"❌ Erreur de lecture fusion {filename}: {e}")

    # Sauvegarde finale
    with open(FINAL_MERGED_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_tracks, f, indent=4, ensure_ascii=False)

    print(f"🎉 SUCCÈS TOTAL !")
    print(f"📊 {len(processed_files)} fichiers fusionnés.")
    print(f"🎵 {len(all_tracks)} morceaux au total dans la base.")
    print(f"💾 Fichier final prêt : {FINAL_MERGED_FILE}")

if __name__ == "__main__":
    process_and_merge()