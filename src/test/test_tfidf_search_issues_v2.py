import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.paths import DATA_DIR


def build_tfidf(repo: str = "STM32CubeH7"):
    path = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"
    docs = json.loads(path.read_text(encoding="utf-8"))

    texts = []
    meta = []

    for d in docs:
        if not d.get("is_valid", True):
            continue
        title = d.get("issue_title") or ""
        body = d.get("clean_text") or ""
        texts.append(title + "\n" + body)
        meta.append(d)

    if not texts:
        raise RuntimeError(f"Aucun texte valide pour {repo}")

    vectorizer = TfidfVectorizer(max_features=8000)
    X = vectorizer.fit_transform(texts)
    return meta, vectorizer, X


def search(query: str, meta, vectorizer, X, top_k: int = 5):
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, X)[0]
    idxs = sims.argsort()[::-1][:top_k]
    results = []
    for i in idxs:
        results.append((sims[i], meta[i]))
    return results


def main():
    repo = "STM32CubeH7"
    meta, vectorizer, X = build_tfidf(repo)

    while True:
        q = input("\nQuestion (enter pour quitter) : ").strip()
        if not q:
            break
        res = search(q, meta, vectorizer, X, top_k=5)
        for score, d in res:
            print(f"\n[score={score:.3f}] #{d['issue_number']} - {d['issue_title']}")
            print(f"  layer={d.get('layer')}, severity={d.get('severity')}, board={d.get('board')}, component={d.get('component')}")
            print(f"  url={d.get('github_url')}")


if __name__ == "__main__":
    main()