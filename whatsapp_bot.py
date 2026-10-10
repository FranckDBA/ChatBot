import os

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request
from fastapi.responses import PlainTextResponse

from report import daily_report, format_whatsapp_report
from whatsapp import send_whatsapp_message


load_dotenv()


app = FastAPI(
    title="WhatsApp Sales Bot",
    version="1.0.0"
)


VERIFY_TOKEN = os.getenv(
    "WHATSAPP_VERIFY_TOKEN"
)


# ==========================================
# Vérification du webhook par Meta
# ==========================================

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(
        default=None,
        alias="hub.mode"
    ),
    hub_verify_token: str = Query(
        default=None,
        alias="hub.verify_token"
    ),
    hub_challenge: str = Query(
        default=None,
        alias="hub.challenge"
    ),
):

    print("🔐 Vérification du webhook...")

    if (
        hub_mode == "subscribe"
        and hub_verify_token == VERIFY_TOKEN
    ):

        print("✅ Webhook vérifié")

        return PlainTextResponse(
            hub_challenge
        )

    print("❌ Vérification échouée")

    return PlainTextResponse(
        "Forbidden",
        status_code=403
    )


# ==========================================
# Réception des messages WhatsApp
# ==========================================

@app.post("/webhook")
async def receive_webhook(
    request: Request
):

    data = await request.json()

    print()
    print("📩 WEBHOOK WHATSAPP")
    print("=" * 50)
    print(data)

    try:

        entries = data.get(
            "entry",
            []
        )

        if not entries:
            return {
                "status": "ignored"
            }

        changes = entries[0].get(
            "changes",
            []
        )

        if not changes:
            return {
                "status": "ignored"
            }

        value = changes[0].get(
            "value",
            {}
        )

        messages = value.get(
            "messages",
            []
        )

        # ==========================================
        # Pas de message
        # ==========================================

        if not messages:

            print(
                "ℹ️ Aucun message à traiter."
            )

            return {
                "status": "ignored"
            }

        message = messages[0]

        phone = message.get(
            "from"
        )

        message_type = message.get(
            "type"
        )

        print(
            "👤 Numéro :",
            phone
        )

        print(
            "📨 Type :",
            message_type
        )

        # ==========================================
        # Message texte
        # ==========================================

        if message_type == "text":

            text = message["text"]["body"].strip()

            command = text.lower()

            print(
                "💬 Message :",
                text
            )

            # ======================================
            # RAPPORT
            # ======================================

            if command in [
                "rapport",
                "report",
                "rapport du jour",
                "rapport jour"
            ]:

                print(
                    "📊 Génération du rapport..."
                )

                report = daily_report()

                response = format_whatsapp_report(
                    report
                )

                send_whatsapp_message(
                    phone,
                    response
                )

            # ======================================
            # BONJOUR
            # ======================================

            elif command in [
                "bonjour",
                "salut",
                "hello",
                "hi"
            ]:

                response = (
                    "👋 Bonjour !\n\n"
                    "Bienvenue dans votre "
                    "assistant de gestion des ventes.\n\n"
                    "📊 *RAPPORT*\n"
                    "Voir le rapport du jour.\n\n"
                    "❓ *AIDE*\n"
                    "Voir les commandes disponibles."
                )

                send_whatsapp_message(
                    phone,
                    response
                )

            # ======================================
            # AIDE
            # ======================================

            elif command in [
                "aide",
                "help"
            ]:

                response = (
                    "🤖 *COMMANDES DISPONIBLES*\n\n"

                    "📊 *RAPPORT*\n"
                    "Rapport des ventes du jour.\n\n"

                    "👋 *BONJOUR*\n"
                    "Message d'accueil.\n\n"

                    "❓ *AIDE*\n"
                    "Afficher cette aide."
                )

                send_whatsapp_message(
                    phone,
                    response
                )

            # ======================================
            # COMMANDE INCONNUE
            # ======================================

            else:

                response = (
                    "🤖 Je n'ai pas compris "
                    "votre commande.\n\n"
                    "Écrivez *AIDE* pour voir "
                    "les commandes disponibles."
                )

                send_whatsapp_message(
                    phone,
                    response
                )

        # ==========================================
        # Image / audio / document / etc.
        # ==========================================

        else:

            print(
                "ℹ️ Message non textuel ignoré."
            )

    except Exception as e:

        print()
        print(
            "❌ ERREUR WEBHOOK"
        )

        print(
            str(e)
        )

    # ==========================================
    # Toujours répondre rapidement à Meta
    # ==========================================

    return {
        "status": "ok"
    }