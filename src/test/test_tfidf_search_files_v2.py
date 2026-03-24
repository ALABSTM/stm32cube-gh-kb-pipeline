import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.paths import DATA_DIR


def build_tfidf_files(repo: str = "STM32CubeH7"):
    """
    Construit un index TF-IDF sur les fichiers V2 (docs_files_<repo>_v2.json).
    Retourne (meta, vectorizer, X) comme pour les issues.
    """
    path = DATA_DIR / f"docs_files_{repo.lower()}_v2.json"
    docs = json.loads(path.read_text(encoding="utf-8"))

    texts = []
    meta = []

    for d in docs:
        if not d.get("is_valid", True):
            continue

        # On peut éventuellement inclure path + file_type pour enrichir le texte
        header = f"{d.get('path', '')}\n[{d.get('file_type', '')}]"
        body = d.get("clean_text") or ""
        texts.append(header + "\n" + body)
        meta.append(d)

    if not texts:
        raise RuntimeError(f"Aucun texte valide pour les fichiers de {repo}")

    vectorizer = TfidfVectorizer(max_features=8000)
    X = vectorizer.fit_transform(texts)
    return meta, vectorizer, X


def search_files(query: str, meta, vectorizer, X, top_k: int = 5):
    """
    Recherche les fichiers les plus pertinents pour une requête.
    """
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, X)[0]
    idxs = sims.argsort()[::-1][:top_k]
    results = []
    for i in idxs:
        results.append((sims[i], meta[i]))
    return results


def main():
    repo = "STM32CubeH7"
    meta, vectorizer, X = build_tfidf_files(repo)

    while True:
        q = input("\nQuestion (enter pour quitter) : ").strip()
        if not q:
            break

        res = search_files(q, meta, vectorizer, X, top_k=5)
        for score, d in res:
            print(f"\n[score={score:.3f}] {d.get('file_type')} - {d.get('path')}")
            print(f"  board={d.get('board')}, component={d.get('component')}, example_name={d.get('example_name')}")
            print("  extrait:")
            clean_text = d.get("clean_text") or ""
            # on affiche juste le début du texte pour comprendre de quoi il parle
            print("   ", clean_text[:300].replace("\n", " ") + "...")
            print("-" * 80)


if __name__ == "__main__":
    main()