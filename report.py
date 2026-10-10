from sqlalchemy import text
from database import engine


def daily_report():

    # ==========================================
    # 1. Résumé global
    # ==========================================

    sales_query = text("""
        SELECT
            COUNT(*) AS nombre_ventes,
            COALESCE(SUM(total), 0) AS chiffre_affaires,
            COALESCE(SUM(cash_tendered), 0) AS total_encaisse,
            COALESCE(SUM(change_amount), 0) AS total_monnaie
        FROM sales
        WHERE DATE(created_at) = CURDATE()
          AND status = 'completed'
    """)

    # ==========================================
    # 2. Nombre total d'articles
    # ==========================================

    items_query = text("""
        SELECT
            COALESCE(SUM(si.quantity), 0) AS articles_vendus
        FROM sale_items si
        INNER JOIN sales s
            ON s.id = si.sale_id
        WHERE DATE(s.created_at) = CURDATE()
          AND s.status = 'completed'
    """)

    # ==========================================
    # 3. Ventes par utilisateur
    # ==========================================

    users_query = text("""
        SELECT
            u.id AS user_id,
            u.name AS vendeur,
            COUNT(s.id) AS nombre_ventes,
            COALESCE(SUM(s.total), 0) AS chiffre_affaires
        FROM sales s
        INNER JOIN users u
            ON u.id = s.user_id
        WHERE DATE(s.created_at) = CURDATE()
          AND s.status = 'completed'
        GROUP BY u.id, u.name
        ORDER BY chiffre_affaires DESC
    """)

    # ==========================================
    # 4. Articles vendus par utilisateur
    # ==========================================

    user_items_query = text("""
        SELECT
            s.user_id,
            COALESCE(SUM(si.quantity), 0) AS articles_vendus
        FROM sales s
        INNER JOIN sale_items si
            ON si.sale_id = s.id
        WHERE DATE(s.created_at) = CURDATE()
          AND s.status = 'completed'
        GROUP BY s.user_id
    """)

    # ==========================================
    # 5. Produits les plus vendus
    # ==========================================

    products_query = text("""
        SELECT
            si.product_name,
            SUM(si.quantity) AS quantite,
            COALESCE(SUM(si.subtotal), 0) AS chiffre_affaires
        FROM sale_items si
        INNER JOIN sales s
            ON s.id = si.sale_id
        WHERE DATE(s.created_at) = CURDATE()
          AND s.status = 'completed'
        GROUP BY si.product_id, si.product_name
        ORDER BY quantite DESC
        LIMIT 10
    """)

    # ==========================================
    # Exécution
    # ==========================================

    with engine.connect() as connection:

        sales = connection.execute(
            sales_query
        ).mappings().first()

        items = connection.execute(
            items_query
        ).mappings().first()

        users = connection.execute(
            users_query
        ).mappings().all()

        user_items = connection.execute(
            user_items_query
        ).mappings().all()

        products = connection.execute(
            products_query
        ).mappings().all()

    # ==========================================
    # Transformer les articles par vendeur
    # ==========================================

    articles_by_user = {
        row["user_id"]: row["articles_vendus"]
        for row in user_items
    }

    # ==========================================
    # Affichage console
    # ==========================================

    print()
    print("📊 RAPPORT JOURNALIER")
    print("=" * 40)

    print(
        "🧾 Nombre de ventes :",
        sales["nombre_ventes"]
    )

    print(
        "📦 Articles vendus :",
        items["articles_vendus"]
    )

    print(
        "💰 Chiffre d'affaires :",
        sales["chiffre_affaires"],
        "FC"
    )

    print(
        "💵 Total encaissé :",
        sales["total_encaisse"],
        "FC"
    )

    print(
        "💸 Monnaie rendue :",
        sales["total_monnaie"],
        "FC"
    )

    # ==========================================
    # Vendeurs
    # ==========================================

    print()
    print("👥 VENDEURS")
    print("-" * 40)

    for user in users:

        nombre_articles = articles_by_user.get(
            user["user_id"],
            0
        )

        print()
        print(f"👤 {user['vendeur']}")

        print(
            f"   🧾 Ventes : {user['nombre_ventes']}"
        )

        print(
            f"   📦 Articles : {nombre_articles}"
        )

        print(
            f"   💰 CA : {user['chiffre_affaires']} FC"
        )

    # ==========================================
    # Produits
    # ==========================================

    print()
    print("🏆 TOP PRODUITS")
    print("-" * 40)

    for index, product in enumerate(
        products,
        start=1
    ):

        print(
            f"{index}. "
            f"{product['product_name']} - "
            f"{product['quantite']} unités - "
            f"{product['chiffre_affaires']} FC"
        )

    return {
        "nombre_ventes": sales["nombre_ventes"],
        "articles_vendus": items["articles_vendus"],
        "chiffre_affaires": sales["chiffre_affaires"],
        "total_encaisse": sales["total_encaisse"],
        "total_monnaie": sales["total_monnaie"],
        "vendeurs": [
            {
                "user_id": user["user_id"],
                "vendeur": user["vendeur"],
                "nombre_ventes": user["nombre_ventes"],
                "articles_vendus": articles_by_user.get(
                    user["user_id"],
                    0
                ),
                "chiffre_affaires": user["chiffre_affaires"],
            }
            for user in users
        ],
        "produits": products,
    }


# ==========================================
# Formatage pour WhatsApp
# ==========================================

def format_whatsapp_report(report):

    message = "📊 *RAPPORT JOURNALIER*\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"

    message += (
        f"🧾 Ventes : {report['nombre_ventes']}\n"
    )

    message += (
        f"📦 Articles vendus : "
        f"{report['articles_vendus']}\n"
    )

    message += (
        f"💰 Chiffre d'affaires : "
        f"{report['chiffre_affaires']} FC\n"
    )

    message += (
        f"💵 Total encaissé : "
        f"{report['total_encaisse']} FC\n"
    )

    message += (
        f"💸 Monnaie rendue : "
        f"{report['total_monnaie']} FC\n"
    )

    # ==========================================
    # Vendeurs
    # ==========================================

    message += "\n👥 *VENDEURS*\n"
    message += "━━━━━━━━━━━━━━━━━━\n"

    if report["vendeurs"]:

        for vendeur in report["vendeurs"]:

            message += (
                f"\n👤 *{vendeur['vendeur']}*\n"
            )

            message += (
                f"🧾 Ventes : "
                f"{vendeur['nombre_ventes']}\n"
            )

            message += (
                f"📦 Articles : "
                f"{vendeur['articles_vendus']}\n"
            )

            message += (
                f"💰 CA : "
                f"{vendeur['chiffre_affaires']} FC\n"
            )

    else:

        message += "\nAucune vente aujourd'hui.\n"

    # ==========================================
    # Produits
    # ==========================================

    message += "\n🏆 *TOP PRODUITS*\n"
    message += "━━━━━━━━━━━━━━━━━━\n"

    if report["produits"]:

        for index, product in enumerate(
            report["produits"],
            start=1
        ):

            message += (
                f"{index}. "
                f"*{product['product_name']}*\n"
            )

            message += (
                f"   📦 {product['quantite']} unités\n"
            )

            message += (
                f"   💰 "
                f"{product['chiffre_affaires']} FC\n"
            )

    else:

        message += "\nAucun produit vendu aujourd'hui.\n"

    message += "\n━━━━━━━━━━━━━━━━━━"
    message += "\n🤖 Rapport automatique"

    return message


# ==========================================
# Exécution directe du fichier
# ==========================================

if __name__ == "__main__":
    daily_report()