from flask import Flask, request, abort
import hmac, hashlib, requests, os

app = Flask(__name__)

WEBHOOK_SECRET = "monsecret"
GITHUB_TOKEN = os.getenv("GITHUB_TOKENn")

def verify_signature(payload, header):
    mac = hmac.new(WEBHOOK_SECRET.encode(), msg=payload, digestmod=hashlib.sha256)
    return hmac.compare_digest("sha256=" + mac.hexdigest(), header or "")

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    if not verify_signature(payload, request.headers.get("X-Hub-Signature-256")):
        abort(403)

    if request.headers.get("X-GitHub-Event") == "issues":
        data = request.get_json(silent=True) or {}
        if data.get("action") == "opened":
            repo = data["repository"]["full_name"]
            issue_number = data["issue"]["number"]
            message = "Merci d’avoir ouvert une issue ! Le bot réfléchit pour te répondre."
            url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
            headers = {"Authorization": f"Bearer {GITHUB_TOKEN}",
                       "Accept": "application/vnd.github+json"}
            requests.post(url, headers=headers, json={"body": message})
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000)