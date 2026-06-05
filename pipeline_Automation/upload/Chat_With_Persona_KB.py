import argparse
import json
import random
import time
from typing import Any, Dict, Optional

import requests
import urllib3

from Get_Persona_KBs import (
    apiKey,
    clientAppName,
    generate_token,
    get_ST_GitHub_Analyzer_kb,
    proxies,
    url,
)

# Disable SSL warnings because existing automation already uses verify=False.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


CHAT_SERVICE_NAME = "chat"
DEFAULT_MAX_RETRIES = 3
DEFAULT_PERSONA = "ST GitHub Analyzer"


def _extract_text_from_chat_response(response_json: Dict[str, Any]) -> Optional[str]:
    """Extract a text answer from possible response formats."""
    if not isinstance(response_json, dict):
        return None

    completion = response_json.get("completion")
    if isinstance(completion, str) and completion.strip():
        return completion.strip()

    def _extract_from_any(node: Any) -> Optional[str]:
        if isinstance(node, str) and node.strip():
            return node.strip()

        if isinstance(node, dict):
            # Prefer assistant message content when role is available.
            role = node.get("role")
            if isinstance(role, str) and role.lower() == "assistant":
                content = node.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

            for key in ("text", "answer", "output_text", "content", "message", "final"):
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

            for key in (
                "completion",
                "message",
                "messages",
                "choices",
                "output",
                "result",
                "results",
                "response",
                "responses",
                "data",
                "payload",
            ):
                if key in node:
                    extracted = _extract_from_any(node[key])
                    if extracted:
                        return extracted

        if isinstance(node, list):
            for item in reversed(node):
                extracted = _extract_from_any(item)
                if extracted:
                    return extracted

        return None

    # Common flat fields.
    for key in ("text", "content", "message", "answer"):
        value = response_json.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

   
    choices = response_json.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            msg = first.get("message")
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

            content = first.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

            text = first.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    # Generic nested messages list.
    messages = response_json.get("messages")
    if isinstance(messages, list):
        for item in reversed(messages):
            if isinstance(item, dict):
                content = item.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()

    return _extract_from_any(response_json)


def call_chat_for_persona(
    user_prompt: str,
    system_prompt: Optional[str] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    use_proxy: bool = False,
    temperature: float = 0.3,
    persona: Optional[str] = None,
    remote_user: Optional[str] = None,
    max_response_tokens: int = 4096,
    response_format: str = "text",
    reasoning_effort: Optional[str] = None,
    debug: bool = False,
) -> Optional[str]:
    """Call ST GitHub Analyzer chat service for the current persona and selected KB."""
    kb = get_ST_GitHub_Analyzer_kb()
    if not kb:
        print("[Chat] Warning: KB ST GitHub Analyzer non trouvee pour la persona.")

    kb_id = kb.get("id") if kb else None
    kb_name = kb.get("name") if kb else None
    selected_persona = (persona or DEFAULT_PERSONA).strip()

    messages: list[Dict[str, Any]] = []
    if system_prompt and system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    messages.append({"role": "user", "content": user_prompt.strip()})

    timestamp_modes = ["seconds", "milliseconds"]

    for attempt in range(1, max_retries + 1):
        for mode_idx, timestamp_mode in enumerate(timestamp_modes):
            timestamp = int(time.time()) if timestamp_mode == "seconds" else int(time.time() * 1000)
            nonce = random.randint(0, 999999)
            token = generate_token(clientAppName, CHAT_SERVICE_NAME, apiKey, timestamp, nonce)

            headers = {
                "Content-Type": "application/json",
                "stchatgpt-auth-token": token,
                "stchatgpt-auth-nonce": str(nonce),
            }

            payload: Dict[str, Any] = {
                "version": 1,
                "clientAppName": clientAppName,
                "service": CHAT_SERVICE_NAME,
                "timestamp": timestamp,
                "messages": messages,
                "temperature": temperature,
                "persona": selected_persona,
                "maxResponseTokens": max_response_tokens,
                "responseFormat": response_format,
            }
            if remote_user and remote_user.strip():
                payload["remoteUser"] = remote_user.strip()
            if reasoning_effort:
                payload["reasoningEffort"] = reasoning_effort

            print(
                f"[Chat] Tentative {attempt}/{max_retries} "
                f"(persona={selected_persona}, timestamp={timestamp_mode}, KB id={kb_id}, name={kb_name})"
            )

            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    verify=False,
                    timeout=120,
                    proxies=proxies if use_proxy else None,
                )

                if response.status_code >= 400:
                    print(f"[Chat] HTTP {response.status_code}: {response.text[:300]}")
                    if attempt < max_retries and response.status_code in {408, 425, 429, 500, 502, 503, 504}:
                        time.sleep(2 ** attempt)
                        break
                    return None

                response_json = response.json()

            except requests.exceptions.RequestException as exc:
                print(f"[Chat] Erreur reseau tentative {attempt}/{max_retries}: {exc}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    break
                return None
            except ValueError:
                print(f"[Chat] Reponse non JSON: {response.text[:300]}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    break
                return None

            error_code = response_json.get("errorCode")
            error_message = str(response_json.get("message") or "")

            if debug:
                print(f"[Chat][Debug] Reponse JSON keys: {list(response_json.keys())}")

            if error_code not in (None, 0):
                print(
                    "[Chat] Erreur API: "
                    f"errorCode={error_code}, message={error_message}"
                )
                # If timestamp format is rejected, retry immediately with the alternate format.
                if error_code == 2000 and "invalid timestamp" in error_message.lower() and mode_idx == 0:
                    print("[Chat] Retest immediat avec timestamp en millisecondes.")
                    continue

                if attempt < max_retries and error_code in {429, 500, 502, 503, 504, "RATE_LIMITED", "TEMPORARY_UNAVAILABLE"}:
                    time.sleep(2 ** attempt)
                    break
                return None

            extracted = _extract_text_from_chat_response(response_json)
            if extracted:
                return extracted

            print("[Chat] Aucun contenu exploitable dans la reponse.")
            if debug:
                print("[Chat][Debug] Reponse JSON complete:")
                print(json.dumps(response_json, ensure_ascii=True, indent=2)[:8000])
            return None

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chat service utilisant la persona et la KB ST GitHub Analyzer"
    )
    parser.add_argument("-q", "--question", help="Question utilisateur")
    parser.add_argument(
        "-s",
        "--system",
        default="",
        help="Contexte systeme ajoute avant la question",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help="Nombre maximum de tentatives",
    )
    parser.add_argument(
        "--use-proxy",
        action="store_true",
        help="Utiliser les proxies definis dans Get_Persona_KBs.py",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Temperature du modele",
    )
    parser.add_argument(
        "--persona",
        default=DEFAULT_PERSONA,
        help="Persona envoyee au service chat",
    )
    parser.add_argument(
        "--remote-user",
        default="",
        help="Utilisateur distant (ex: john.smith@st.com)",
    )
    parser.add_argument(
        "--max-response-tokens",
        type=int,
        default=4096,
        help="Nombre max de tokens en sortie",
    )
    parser.add_argument(
        "--response-format",
        choices=["text", "json_object"],
        default="text",
        help="Format de reponse attendu",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=["none", "low", "medium", "high"],
        default=None,
        help="Niveau de raisonnement (si supporte par le modele)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Affiche des details de la reponse brute pour debug",
    )

    args = parser.parse_args()

    if args.question:
        answer = call_chat_for_persona(
            user_prompt=args.question,
            system_prompt=args.system,
            max_retries=args.max_retries,
            use_proxy=args.use_proxy,
            temperature=args.temperature,
            persona=args.persona,
            remote_user=args.remote_user or None,
            max_response_tokens=args.max_response_tokens,
            response_format=args.response_format,
            reasoning_effort=args.reasoning_effort,
            debug=args.debug,
        )
        if answer:
            print("\nAssistant:\n" + answer)
        else:
            print("\nEchec de generation de reponse.")
        return

    print("Mode interactif (tape 'exit' pour quitter)")
    while True:
        question = input("\nVous: ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            break

        answer = call_chat_for_persona(
            user_prompt=question,
            system_prompt=args.system,
            max_retries=args.max_retries,
            use_proxy=args.use_proxy,
            temperature=args.temperature,
            persona=args.persona,
            remote_user=args.remote_user or None,
            max_response_tokens=args.max_response_tokens,
            response_format=args.response_format,
            reasoning_effort=args.reasoning_effort,
            debug=args.debug,
        )

        if answer:
            print("\nAssistant:\n" + answer)
        else:
            print("\nAssistant: Echec de generation de reponse.")


if __name__ == "__main__":
    main()
