import json
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.utils.paths import DATA_DIR, get_config_path


def load_config() -> dict:
    cfg_path = get_config_path()
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def compute_related_issues_for_repo(repo: str, top_k: int = 3, min_sim: float = 0.4) -> None:
    docs_file = DATA_DIR / f"docs_issues_{repo.lower()}_v2.json"
    if not docs_file.exists():
        print(f"[WARN] docs_issues_v2 introuvable pour {repo} : {docs_file}")
        return

    docs: List[dict] = json.loads(docs_file.read_text(encoding="utf-8"))

    texts = []
    ids = []
    valid_idx = [] 

    for idx, d in enumerate(docs):
        if not d.get("is_valid", True):
            continue
        ids.append(d["id"])
        valid_idx.append(idx)
        title = d.get("issue_title") or ""
        body = d.get("clean_text") or ""
        texts.append(title + "\n" + body)

    if not texts:
        print(f"[WARN] Aucun texte valide pour {repo}")
        return

    print(f"[SIM] TF-IDF sur {len(texts)} issues valides pour {repo}...")
    vectorizer = TfidfVectorizer(max_features=5000)
    X = vectorizer.fit_transform(texts)

    sim_matrix = cosine_similarity(X)

    id_to_related: dict[str, list[str]] = {doc_id: [] for doc_id in ids}

    for i, doc_id in enumerate(ids):
        sims = sim_matrix[i]
        indices = sims.argsort()[::-1]
        related: list[str] = []
        for j in indices:
            if j == i:
                continue
            if sims[j] < min_sim:
                break
            related.append(ids[j])
            if len(related) >= top_k:
                break
        id_to_related[doc_id] = related

   
    for idx, d in enumerate(docs):
        doc_id = d["id"]
        d["related_issue_ids"] = id_to_related.get(doc_id, [])

    out_file = DATA_DIR / f"docs_issues_{repo.lower()}_v2_sim.json"
    out_file.write_text(
        json.dumps(docs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[SIM] docs_issues_v2 enrichis avec related_issue_ids → {out_file}")


def main() -> None:
    cfg = load_config()
    repos = cfg["repos"]
    for repo in repos:
        compute_related_issues_for_repo(repo, top_k=3, min_sim=0.4)

    print("Terminé similarité V2.")


if __name__ == "__main__":
    main()