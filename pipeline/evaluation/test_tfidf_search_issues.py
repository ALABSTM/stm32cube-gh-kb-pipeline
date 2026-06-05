import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from shared.utils.paths import DATA_DIR


def build_tfidf(repo: str = "STM32CubeH7"):
    path = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"
    docs = json.loads(path.read_text(encoding="utf-8"))

    texts = []
    ids = []
    meta = []

    for d in docs:
        if not d.get("is_valid", True):
            continue
        ids.append(d["id"])
        meta.append(d)
        title = d.get("issue_title") or ""
        body = d.get("clean_text") or ""
        texts.append(title + "\n" + body)

    vectorizer = TfidfVectorizer(max_features=8000)
    x_matrix = vectorizer.fit_transform(texts)
    return ids, meta, vectorizer, x_matrix


def search(query: str, ids, meta, vectorizer, x_matrix, top_k: int = 5):
    q_vec = vectorizer.transform([query])
    sims = cosine_similarity(q_vec, x_matrix)[0]
    idxs = sims.argsort()[::-1][:top_k]
    return [(sims[i], meta[i]) for i in idxs]


def main() -> None:
    repo = "STM32CubeH7"
    ids, meta, vectorizer, x_matrix = build_tfidf(repo)

    while True:
        q = input("\nQuestion (enter to quit): ").strip()
        if not q:
            break
        res = search(q, ids, meta, vectorizer, x_matrix, top_k=10)
        for score, d in res:
            print(f"\n[score={score:.3f}] {d['issue_number']} - {d['issue_title']}")
            print(
                "  "
                f"layer={d.get('layer')}, severity={d.get('severity')}, "
                f"board={d.get('board')}, component={d.get('component')}"
            )
            print(f"  url={d.get('github_url')}")


if __name__ == "__main__":
    main()
