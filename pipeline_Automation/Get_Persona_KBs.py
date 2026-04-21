import time
import random
import hashlib
import requests
import urllib3
 
"""
This script gets the list of knowledge bases (KBs) linked to a persona
using a secure API with authentication.
 
It retries requests if they fail and supports optional proxy settings.
 
Run the script to print the KB list.
"""
 
# Désactiver les warnings SSL (à utiliser avec précaution)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
 
 
clientAppName = "mdrf_st_github_analyzer"
apiKey = "2d4fb50a-a6be-49fe-8054-2f12e880686c"
serviceName = "kb"
url = "https://api-ai-bridge.st.com/chatgpt/api/client-apps"
 
# Proxy optionnel (à modifier ou supprimer si inutile)
proxies = {
    "http": "http://185.46.212.88:80",
    "https": "http://185.46.212.88:80"
}
def generate_token(clientAppName, serviceName, apiKey, timestamp, nonce):
    """
    Génère le token SHA1 pour l'authentification.
    """
    data_string = f"{clientAppName}_{serviceName}_{apiKey}_{timestamp}_{nonce}"
    return hashlib.sha1(data_string.encode('utf-8')).hexdigest()
 
def call_api(request_body, max_retries=3):
    """
    Envoie la requête POST à l'API avec gestion des retries.
    """
    for attempt in range(1, max_retries + 1):
        timestamp = request_body.get("timestamp", int(time.time()))
        nonce = random.randint(0, 999999)
        token = generate_token(clientAppName, serviceName, apiKey, timestamp, nonce)
 
        headers = {
            "Content-Type": "application/json",
            "stchatgpt-auth-token": token,
            "stchatgpt-auth-nonce": str(nonce)
        }
 
        try:
            response = requests.post(
                url,
                json=request_body,
                headers=headers,
                verify=False,  # Désactiver la vérification SSL (pas recommandé en prod)
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            else:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
 
 
 
#  if __name__ == "__main__":
#  try:
 #       get_kb_list_for_persona()
  #  except Exception as e:
   #     print(f"Failed to retrieve KB list: {e}")
def get_kb_list_for_persona():
    """
    Appelle l'API GitHub analyzer pour récupérer la liste des KBs associées
    à la persona / clientAppName.
 
    Retourne une liste de dictionnaires Python (kbs).
    """
    request_body = {
        "service": "kb",
        "type": "kb-list",
        "clientAppName": clientAppName,
        "version": 1,
        "timestamp": int(time.time())
    }
 
    response = call_api(request_body)
 
    if response.get("errorCode"):
        print(f"API error: {response.get('message')}")
        return []
 
    kbs = response.get("kbs", [])
    return kbs
 
def get_ST_GitHub_Analyzer_kb():
    """
    Retourne la KB 'ST GitHub Analyzer' sous forme de dict Python.
    Si elle n'est pas trouvée, retourne None.
    """
    kbs = get_kb_list_for_persona()
    for kb in kbs:
        # Deux critères au cas où
        if kb.get("id") == 793 or kb.get("name") == "ST GITHUB ANALYZER_UNSTRUCTURED":
            return kb
    return None
 
if __name__ == "__main__":
    kb = get_ST_GitHub_Analyzer_kb()
    if not kb:
        print("KB ST GitHub Analyzer non trouvée")
    else:
        print("KBs associated with persona:")
        print("-", kb)
        print("\nRésumé :")
        print("  id       :", kb.get("id"))
        print("  name     :", kb.get("name"))
        print("  kbType   :", kb.get("kbType"))
        print("  dataType :", kb.get("dataType"))
        print("  #dataSources :", len(kb.get("dataSources", [])))