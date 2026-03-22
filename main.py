
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os

# ============================================================
# ⚙️ CONFIGURATION — Modifie ces infos avec les tiennes
# ============================================================
TOKEN = "8718072594:AAE08e1vffzrfsDvu5fusN3CJmckfe3Kmdo"

MON_NOM        = "Paymaster Cameroun"
MON_TELEPHONE  = "+237 659415944"
WAVE_NUMERO    = "+237 651315722"
OM_NUMERO      = "+237 651315722"   # Orange Money Cameroun
MTN_NUMERO     = "+237 651315722"   # MTN Mobile Money Cameroun
DEVISE         = "FCFA"

# ============================================================
# 📦 CATALOGUE DES SERVICES
# Disponible = True  → le client peut payer
# Disponible = False → le bot dit "non disponible"
# Tu peux modifier les prix et la disponibilité à tout moment
# ============================================================
CATALOGUE = {
    "eneo": {
        "nom": "⚡ Électricité ENEO",
        "description": "Paiement facture ENEO Cameroun",
        "prix_min": 1000,
        "disponible": True,
        "emoji": "⚡"
    },
    "camwater": {
        "nom": "💧 Eau CAMWATER / CDE",
        "description": "Paiement facture eau CDE/CAMWATER",
        "prix_min": 1000,
        "disponible": True,
        "emoji": "💧"
    },
    "mtn_internet": {
        "nom": "🌐 Internet / Téléphone MTN",
        "description": "Recharge internet ou crédit MTN",
        "prix_min": 500,
        "disponible": True,
        "emoji": "🌐"
    },
    "orange_internet": {
        "nom": "🟠 Internet / Téléphone Orange",
        "description": "Recharge internet ou crédit Orange",
        "prix_min": 500,
        "disponible": True,
        "emoji": "🟠"
    },
    "canal_plus": {
        "nom": "📺 Canal+ / StarTimes",
        "description": "Renouvellement abonnement TV",
        "prix_min": 5000,
        "disponible": True,
        "emoji": "📺"
    },
    "autre": {
        "nom": "🔧 Autre service",
        "description": "Autre paiement personnalisé",
        "prix_min": 500,
        "disponible": True,
        "emoji": "🔧"
    },
}
# ============================================================

logging.basicConfig(level=logging.INFO)

# États
CHOISIR_SERVICE, ENTRER_NUMERO_COMPTEUR, ENTRER_MONTANT, CHOISIR_PAIEMENT, CONFIRMER = range(5)


def generer_facture(numero, client, service_nom, description, numero_compteur, montant, methode):
    """Génère un PDF de facture professionnel."""
    filename = f"facture_{numero}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    # En-tête
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                  fontSize=24, textColor=colors.HexColor('#0066cc'),
                                  spaceAfter=5, alignment=1)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=10, textColor=colors.grey, alignment=1)
    elements.append(Paragraph("🧾 REÇU DE PAIEMENT", title_style))
    elements.append(Paragraph(f"{MON_NOM} — {MON_TELEPHONE}", sub_style))
    elements.append(Spacer(1, 0.5*cm))

    # Ligne séparatrice
    elements.append(Table([['']], colWidths=[17*cm],
                           style=[('LINEABOVE', (0,0), (-1,0), 1.5, colors.HexColor('#0066cc'))]))
    elements.append(Spacer(1, 0.4*cm))

    # Infos facture
    info_data = [
        ["📋 Facture N°", f"#{numero}"],
        ["📅 Date & Heure", datetime.now().strftime("%d/%m/%Y à %H:%M")],
        ["👤 Client", client],
        ["📌 Service", service_nom],
        ["🔢 N° Compteur / Référence", numero_compteur],
    ]
    info_table = Table(info_data, colWidths=[6*cm, 11*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (0,-1), colors.grey),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f5f9ff')]),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.8*cm))

    # Tableau montant
    elements.append(Paragraph("💰 Détail du paiement", ParagraphStyle('H3', parent=styles['Heading3'],
                                                                        textColor=colors.HexColor('#0066cc'))))
    elements.append(Spacer(1, 0.3*cm))

    detail_data = [
        ["Description", "Montant"],
        [description, f"{montant:,} {DEVISE}"],
    ]
    detail_table = Table(detail_data, colWidths=[12*cm, 5*cm])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white]),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 0.3*cm))

    # Total
    total_table = Table([["✅ TOTAL PAYÉ", f"{montant:,} {DEVISE}"]], colWidths=[12*cm, 5*cm])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#00aa44')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 13),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 0.5*cm))

    # Mode de paiement
    elements.append(Paragraph(f"💳 Méthode de paiement : <b>{methode}</b>",
                               ParagraphStyle('pay', parent=styles['Normal'], fontSize=10)))
    elements.append(Spacer(1, 1*cm))

    # Pied de page
    footer = ParagraphStyle('Footer', parent=styles['Normal'],
                             fontSize=9, textColor=colors.grey, alignment=1)
    elements.append(Table([['']], colWidths=[17*cm],
                           style=[('LINEABOVE', (0,0), (-1,0), 0.5, colors.lightgrey)]))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph("✅ Ce reçu confirme votre paiement. Conservez-le précieusement.", footer))
    elements.append(Paragraph(f"{MON_NOM} — {MON_TELEPHONE} | Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", footer))

    doc.build(elements)
    return filename


# ============================================================
# HANDLERS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal avec tous les services."""
    keyboard = []
    for key, service in CATALOGUE.items():
        statut = "✅" if service["disponible"] else "❌"
        keyboard.append([InlineKeyboardButton(
            f"{statut} {service['nom']}",
            callback_data=f"svc_{key}"
        )])

    await update.message.reply_text(
        f"👋 Bienvenue sur *{MON_NOM}* !\n\n"
        "🤖 Votre assistant de paiement automatique *24h/24h - 7j/7*\n\n"
        "📌 Choisissez votre service :\n"
        "✅ = Disponible  |  ❌ = Non disponible",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOISIR_SERVICE


async def choisir_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Vérifie la disponibilité du service choisi."""
    query = update.callback_query
    await query.answer()
    key = query.data.split("_", 1)[1]
    service = CATALOGUE.get(key)

    if not service:
        await query.edit_message_text("❌ Service introuvable. Tapez /start.")
        return ConversationHandler.END

    # ⚠️ SERVICE NON DISPONIBLE
    if not service["disponible"]:
        keyboard = [[InlineKeyboardButton("🔙 Retour au menu", callback_data="retour")]]
        await query.edit_message_text(
            f"⛔ *Service non disponible*\n\n"
            f"{service['emoji']} *{service['nom']}*\n\n"
            f"😔 Désolé, ce service n'est pas disponible pour le moment.\n"
            f"Veuillez réessayer plus tard ou choisir un autre service.\n\n"
            f"🕐 Notre équipe travaille à rétablir ce service.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOISIR_SERVICE

    # ✅ SERVICE DISPONIBLE
    context.user_data['service_key'] = key
    context.user_data['service'] = service
    context.user_data['client'] = query.from_user.first_name or "Client"

    await query.edit_message_text(
        f"✅ *{service['nom']}*\n\n"
        f"📋 {service['description']}\n\n"
        f"🔢 Entrez votre *numéro de compteur / référence* :\n"
        f"_Ex: 1234567890_",
        parse_mode="Markdown"
    )
    return ENTRER_NUMERO_COMPTEUR


async def retour_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retour au menu principal."""
    query = update.callback_query
    await query.answer()
    keyboard = []
    for key, service in CATALOGUE.items():
        statut = "✅" if service["disponible"] else "❌"
        keyboard.append([InlineKeyboardButton(
            f"{statut} {service['nom']}",
            callback_data=f"svc_{key}"
        )])
    await query.edit_message_text(
        f"📌 Choisissez votre service :\n✅ = Disponible  |  ❌ = Non disponible",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOISIR_SERVICE


async def entrer_numero_compteur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enregistre le numéro de compteur."""
    numero = update.message.text.strip()
    if len(numero) < 3:
        await update.message.reply_text("❌ Numéro trop court. Réessayez :")
        return ENTRER_NUMERO_COMPTEUR

    context.user_data['numero_compteur'] = numero
    service = context.user_data['service']

    await update.message.reply_text(
        f"✅ Référence enregistrée : *{numero}*\n\n"
        f"💰 Entrez le *montant* à payer en {DEVISE} :\n"
        f"_Minimum : {service['prix_min']:,} {DEVISE}_",
        parse_mode="Markdown"
    )
    return ENTRER_MONTANT


async def entrer_montant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Valide le montant entré."""
    try:
        montant = int(update.message.text.strip().replace(" ", "").replace(",", ""))
        prix_min = context.user_data['service']['prix_min']
        if montant < prix_min:
            await update.message.reply_text(
                f"❌ Montant minimum : *{prix_min:,} {DEVISE}*. Réessayez :",
                parse_mode="Markdown"
            )
            return ENTRER_MONTANT
        context.user_data['montant'] = montant
    except ValueError:
        await update.message.reply_text("❌ Entrez un nombre valide. Ex: *5000*", parse_mode="Markdown")
        return ENTRER_MONTANT

    keyboard = [
        [InlineKeyboardButton("📱 MTN Mobile Money", callback_data="pay_MTN Mobile Money")],
        [InlineKeyboardButton("🟠 Orange Money", callback_data="pay_Orange Money")],
    ]
    await update.message.reply_text(
        f"💳 *Choisissez votre méthode de paiement :*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOISIR_PAIEMENT


async def choisir_paiement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les instructions de paiement."""
    query = update.callback_query
    await query.answer()
    methode = query.data.split("_", 1)[1]
    context.user_data['methode'] = methode
    montant = context.user_data['montant']
    service = context.user_data['service']

    numeros = {
        "MTN Mobile Money": MTN_NUMERO,
        "Orange Money": OM_NUMERO,
    }
    numero = numeros.get(methode, "N/A")

    await query.edit_message_text(
        f"📋 *Récapitulatif de votre commande*\n\n"
        f"{service['emoji']} Service : *{service['nom']}*\n"
        f"🔢 Référence : *{context.user_data['numero_compteur']}*\n"
        f"💰 Montant : *{montant:,} {DEVISE}*\n"
        f"📱 Méthode : *{methode}*\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📲 *Instructions de paiement :*\n"
        f"1️⃣ Ouvrez votre application *{methode}*\n"
        f"2️⃣ Envoyez *{montant:,} {DEVISE}* au numéro :\n"
        f"    📞 *{numero}*\n"
        f"3️⃣ Notez votre *référence de transaction*\n"
        f"4️⃣ Cliquez ✅ ci-dessous après paiement",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ J'ai payé — Recevoir ma facture", callback_data="confirmer")],
            [InlineKeyboardButton("❌ Annuler", callback_data="annuler_pay")]
        ])
    )
    return CONFIRMER


async def confirmer_paiement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Génère et envoie la facture PDF."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Génération de votre reçu en cours... 🧾")

    numero_facture = datetime.now().strftime("%Y%m%d%H%M%S")
    client = context.user_data.get('client', 'Client')
    service = context.user_data.get('service', {})
    numero_compteur = context.user_data.get('numero_compteur', 'N/A')
    montant = context.user_data.get('montant', 0)
    methode = context.user_data.get('methode', '')

    try:
        pdf_path = generer_facture(
            numero_facture, client,
            service.get('nom', 'Service'),
            service.get('description', ''),
            numero_compteur, montant, methode
        )
        await query.message.reply_document(
            document=open(pdf_path, 'rb'),
            filename=f"Recu_{numero_facture}.pdf",
            caption=(
                f"✅ *Paiement confirmé !*\n\n"
                f"🧾 Reçu N° *{numero_facture}*\n"
                f"{service.get('emoji','')  } {service.get('nom','')}\n"
                f"💰 *{montant:,} {DEVISE}* payés via {methode}\n\n"
                f"Merci de nous faire confiance ! 🙏\n"
                f"Tapez /start pour un nouveau paiement."
            ),
            parse_mode="Markdown"
        )
        os.remove(pdf_path)
    except Exception as e:
        await query.message.reply_text(f"❌ Erreur : {e}")

    return ConversationHandler.END


async def annuler_paiement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Paiement annulé. Tapez /start pour recommencer.")
    return ConversationHandler.END


async def annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Annulé. Tapez /start pour recommencer.")
    return ConversationHandler.END


# ============================================================
# LANCEMENT
# ============================================================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOISIR_SERVICE: [
                CallbackQueryHandler(choisir_service, pattern="^svc_"),
                CallbackQueryHandler(retour_menu, pattern="^retour$"),
            ],
            ENTRER_NUMERO_COMPTEUR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, entrer_numero_compteur)
            ],
            ENTRER_MONTANT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, entrer_montant)
            ],
            CHOISIR_PAIEMENT: [
                CallbackQueryHandler(choisir_paiement, pattern="^pay_")
            ],
            CONFIRMER: [
                CallbackQueryHandler(confirmer_paiement, pattern="^confirmer$"),
                CallbackQueryHandler(annuler_paiement, pattern="^annuler_pay$"),
            ],
        },
        fallbacks=[CommandHandler("annuler", annuler)],
    )

    app.add_handler(conv)
    print("🤖 Paymaster Cameroun démarré 24h/24h !")
    print("✅ En attente de clients...")
    app.run_polling()
