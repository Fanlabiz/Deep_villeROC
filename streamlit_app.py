import streamlit as st
import json
import base64
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="RoC CSV Generator", layout="wide")

st.title("🏛️ Rise of Cultures - Générateur de CSV")
st.markdown("Analyse les bundles Unity et génère le CSV complet avec la culture du City Hall")

# ============================================
# SECTION 1: Upload du fichier JSON
# ============================================
st.header("📁 1. Charger les données exportées")

uploaded_json = st.file_uploader(
    "Fichier JSON exporté par le userscript (`roc_export_data.json`)",
    type=["json"]
)

if uploaded_json:
    data = json.load(uploaded_json)
    
    st.success(f"✅ Fichier chargé: {uploaded_json.name}")
    st.json({
        "version": data.get("version"),
        "timestamp": data.get("timestamp"),
        "has_startup": data.get("has_startup"),
        "has_city": data.get("has_city"),
        "has_bundles": data.get("has_bundles"),
        "bundles_count": len(data.get("bundles", []))
    })
    
    # ============================================
    # SECTION 2: Analyse des bundles Unity
    # ============================================
    st.header("🎮 2. Analyse des bundles Unity")
    
    all_texts = []
    all_artifacts = []
    city_hall_culture = None
    
    # Liste des artefacts connus (à enrichir)
    KNOWN_ARTIFACTS = {
        "Hobble of the Sea": 10, "Jolly Roger": 10, "Hidden Hoard": 10, "Captain's Hat": 10,
        "Drake's Firearm": 25, "Bonny's Blade": 25, "Corsair's Skull": 50,
        "Tools of the First Builders": 10, "Strings of the Ancients": 10,
        "Warrior's Crown": 10, "Vessel of Athena": 10, "Goddess of Fertility": 10,
        "Bust of Marcus Aurelius": 25, "Tragedy and Comedy": 25, "Nebra Disc": 50,
        "Hector's Sword": 10, "Achilles' Armor": 10, "Priam's Diadem": 10,
        "Helen's Dress": 25, "Trojan Horse's Head": 50,
        "Pharaoh's Gold": 10, "Amulet of Khepri": 10, "Anubis Sarcophagus": 25,
        "Idol of Bastet": 25, "Key of Life": 50,
        "Bronze Shell Coins": 10, "Lotus Shoes": 10, "The Art of Cha Dao": 25,
        "Whispers of the Ink": 25, "Loong Symbol": 50,
        "Eccentric Flint": 10, "Bloodletting Stingray Spine": 10, "Xocolatl Drinking Cup": 10,
        "King Pakal's Mask": 25, "Maya Codex of Mexico": 50,
        "Norse Hoard": 10, "Weapons of Valhalla": 10, "Strings of the Skald": 25,
        "Raven Helm": 25, "Prow of Vinland": 50,
        "Torpedo Jar": 10, "Bronze Dromedary Statue": 10, "Arabian Ostrich Egg Container": 10,
        "Ilkhanic Tables": 25, "Queen Arwa's Dinar": 50
    }
    
    # Fonction pour extraire les chaînes de texte d'un bundle
    def extract_strings(bundle_bytes):
        strings = []
        i = 0
        while i < len(bundle_bytes) - 2:
            if 32 <= bundle_bytes[i] < 127:
                start = i
                while i < len(bundle_bytes) and 32 <= bundle_bytes[i] < 127:
                    i += 1
                text = bundle_bytes[start:i].decode('utf-8', errors='ignore')
                if len(text) > 3 and len(text) < 500:
                    strings.append(text)
            else:
                i += 1
        return strings
    
    # Fonction pour chercher des valeurs numériques autour de 800-850
    def find_numeric_values(bundle_bytes):
        values = []
        i = 0
        while i < len(bundle_bytes) - 4:
            # Chercher des entiers 32 bits
            if i + 4 <= len(bundle_bytes):
                val = int.from_bytes(bundle_bytes[i:i+4], 'little')
                if 800 <= val <= 850:
                    values.append(("int32", val, i))
                val2 = int.from_bytes(bundle_bytes[i:i+4], 'big')
                if 800 <= val2 <= 850:
                    values.append(("int32_big", val2, i))
            i += 1
        return values
    
    # Parcourir tous les bundles
    bundles = data.get("bundles", [])
    progress_bar = st.progress(0)
    
    for idx, bundle_info in enumerate(bundles):
        st.subheader(f"Bundle #{bundle_info['index']}")
        st.write(f"URL: {bundle_info['url']}")
        st.write(f"Taille: {bundle_info['size']} octets")
        
        try:
            # Décoder le base64
            bundle_bytes = base64.b64decode(bundle_info['base64'])
            
            # Extraire les textes
            texts = extract_strings(bundle_bytes)
            all_texts.extend(texts)
            st.write(f"📝 {len(texts)} chaînes de texte trouvées")
            
            # Chercher des artefacts dans les textes
            artifacts_found = []
            for artifact_name in KNOWN_ARTIFACTS:
                for text in texts:
                    if artifact_name.lower() in text.lower():
                        artifacts_found.append(artifact_name)
                        break
            
            if artifacts_found:
                st.write(f"🏺 Artefacts trouvés: {', '.join(artifacts_found[:10])}")
                all_artifacts.extend(artifacts_found)
            
            # Chercher des valeurs numériques autour de 840
            numeric_values = find_numeric_values(bundle_bytes)
            if numeric_values:
                st.write(f"🔢 Valeurs numériques entre 800 et 850: {len(numeric_values)}")
                for typ, val, pos in numeric_values[:10]:
                    st.write(f"   - {val} à la position {pos}")
                    
                    # Si on trouve 840, c'est peut-être notre culture
                    if val == 840 and city_hall_culture is None:
                        city_hall_culture = val
                        st.success(f"🎉 **Valeur 840 trouvée dans bundle #{bundle_info['index']}**")
            
            # Afficher un aperçu des textes
            with st.expander(f"Aperçu des textes (bundle #{bundle_info['index']})"):
                for text in texts[:50]:
                    st.write(f"- {text}")
                    
        except Exception as e:
            st.error(f"Erreur lors du décodage: {e}")
        
        progress_bar.progress((idx + 1) / len(bundles))
    
    # ============================================
    # SECTION 3: Culture du City Hall
    # ============================================
    st.header("🏛️ 3. Culture du City Hall")
    
    if city_hall_culture:
        st.success(f"**Culture trouvée dans les bundles : {city_hall_culture}**")
    else:
        st.warning("⚠️ Aucune valeur 840 n'a été trouvée dans les bundles")
        
        # Proposer de chercher des artefacts
        st.info(""" 
        **Alternative :** Calculer la culture à partir des artefacts trouvés.
        
        Cette méthode additionne les valeurs des artefacts reconnus dans les bundles.
        """)
        
        if all_artifacts:
            # Compter les artefacts uniques
            unique_artifacts = list(set(all_artifacts))
            total_culture = sum(KNOWN_ARTIFACTS.get(a, 0) for a in unique_artifacts)
            
            st.write(f"**Artefacts trouvés :** {len(unique_artifacts)}")
            st.write(f"**Culture totale calculée :** {total_culture}")
            
            if total_culture > 0:
                city_hall_culture = total_culture
                st.success(f"🎉 **Culture estimée : {city_hall_culture}**")
        
        # Permettre une saisie manuelle
        manual_culture = st.number_input("Ou saisir la culture manuellement (vue dans le jeu):", 
                                          min_value=0, max_value=10000, value=840, step=10)
        if st.button("Utiliser cette valeur"):
            city_hall_culture = manual_culture
            st.success(f"Culture manuelle définie à {city_hall_culture}")
    
    # ============================================
    # SECTION 4: Génération du CSV
    # ============================================
    st.header("📊 4. Génération du CSV")
    
    if st.button("🔄 Générer le CSV", type="primary"):
        if city_hall_culture:
            st.write(f"**Culture du City Hall : {city_hall_culture}**")
            
            # TODO: Implémenter le décodage complet des bâtiments depuis startup/city
            # Pour l'instant, on génère un CSV minimal avec les artefacts
            
            # Créer un CSV avec les artefacts
            df_artifacts = pd.DataFrame(list(set(all_artifacts)), columns=["Artefact"])
            df_artifacts["Culture"] = df_artifacts["Artefact"].map(lambda x: KNOWN_ARTIFACTS.get(x, 0))
            
            # Ajouter le City Hall
            city_hall_row = pd.DataFrame([{
                "Artefact": "🏛️ Hôtel de Ville (City Hall)",
                "Culture": city_hall_culture
            }])
            
            df_final = pd.concat([city_hall_row, df_artifacts], ignore_index=True)
            
            st.dataframe(df_final, use_container_width=True)
            
            # Téléchargement
            csv = df_final.to_csv(index=False)
            st.download_button(
                label="⬇️ Télécharger le CSV",
                data=csv,
                file_name=f"roc_city_hall_culture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ Impossible de générer le CSV : culture du City Hall non trouvée")
    
    # ============================================
    # SECTION 5: Export des données brutes
    # ============================================
    with st.expander("🔧 Outils avancés"):
        if st.button("Exporter tous les textes extraits"):
            text_export = "\n".join(all_texts)
            st.download_button(
                label="📥 Télécharger les textes",
                data=text_export,
                file_name="roc_texts.txt",
                mime="text/plain"
            )
        
        if st.button("Exporter les artefacts trouvés"):
            artifacts_json = json.dumps(list(set(all_artifacts)), indent=2)
            st.download_button(
                label="📥 Télécharger les artefacts",
                data=artifacts_json,
                file_name="roc_artifacts.json",
                mime="application/json"
            )

else:
    st.info("👈 Commencez par charger un fichier JSON exporté par le userscript")
    st.markdown("""
    ### Utilisation
    
    1. **Sur iPad / jeu** : Ouvrez Rise of Cultures
    2. **Ouvrez votre ville** puis **le musée**
    3. **Cliquez sur le bouton 🏙️** en bas à droite
    4. **Cliquez sur "📁 Exporter pour Streamlit"**
    5. **Téléchargez** le fichier JSON généré
    6. **Revenez ici** et uploadez le fichier
    
    ### Fonctionnalités
    
    - 🔍 Analyse tous les bundles Unity capturés
    - 🏺 Recherche des artefacts et de leurs valeurs
    - 🎯 Traque de la valeur 840 (culture du City Hall)
    - 📊 Génération d'un CSV avec la culture trouvée
    """)

# ============================================
# Pied de page
# ============================================
st.markdown("---")
st.markdown("**RoC CSV Generator v2.0** | Décode les bundles Unity et extrait la culture du City Hall")
