import logging
import os
import json
from datetime import datetime
from threading import Thread
from flask import Flask
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ============================================================
# ⚙️ CONFIGURATION — Modifie ces infos avec les tiennes
# ============================================================
web_app = Flask(_name_)
@web_app.route('/')
def health_check():
    return "Paymaster Bot is Runing!",200
def run_flask():
    variable PORT(souvent 10000)
    port = int(os.environ.get("PORT",10000))
    web_app.run(host="0.0.0.0",port=port)
TOKEN = os.environ.get("BOT_TOKEN")  # ✅ Sécurisé via variable Railway

MON_NOM        = "Paymaster Cameroun"
MON_TELEPHONE  = "+237 659415944"
WAVE_NUMERO    = "+237 651315722"
OM_NUMERO      = "+237 651315722"   # Orange Money
MTN_NUMERO     = "+237 651315722"   # MTN Mobile Money
DEVISE         = "FCFA"
ADMIN_ID       = None  # Mets ton ID Telegram ici (ex: 123456789)

# Fichier pour stocker les transactions
DATA_FILE = "transactions.json"

# ============================================================
# États de la conversation
# ============================================================
(
    MENU_PRINCIPAL,
    SAISIE_CLIENT,
    SAISIE_SERVICE,
    SAISIE_MONTANT,
    SAISIE_PAIEMENT,
    CONFIRMATION,
) = range(6)

# ============================================================
# Logging
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# Utilitaires — gestion des données
# ============================================================
def charger_transactions():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_transaction(transaction):
    transactions = charger_transactions()
    transactions.append(transaction)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)

def generer_numero_facture():
    transactions = charger_transactions()
    numero = len(transactions) + 1
    return f"PM-{datetime.now().year}-{numero:04d}"

# ============================================================
# Génération de la facture PDF — Style ENEO
# ============================================================
def generer_facture_pdf(data: dict) -> str:
    filename = f"facture_{data['numero']}.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    # Couleurs ENEO
    VERT_ENEO    = colors.HexColor("#2E7D32")
    VERT_CLAIR   = colors.HexColor("#A5D6A7")
    VERT_HEADER  = colors.HexColor("#1B5E20")
    JAUNE_DATE   = colors.HexColor("#F9A825")
    GRIS_CLAIR   = colors.HexColor("#F5F5F5")
    BLANC        = colors.white
    NOIR         = colors.black

    styles = getSampleStyleSheet()
    story = []

    # ── Style textes ─────────────────────────────────────────
    style_titre = ParagraphStyle(
        "titre", fontName="Helvetica-Bold", fontSize=16,
        textColor=VERT_HEADER, alignment=TA_LEFT
    )
    style_sous_titre = ParagraphStyle(
        "sous_titre", fontName="Helvetica", fontSize=9,
        textColor=colors.grey, alignment=TA_LEFT
    )
    style_centre = ParagraphStyle(
        "centre", fontName="Helvetica", fontSize=9,
        textColor=NOIR, alignment=TA_CENTER
    )
    style_bold_centre = ParagraphStyle(
        "bold_centre", fontName="Helvetica-Bold", fontSize=10,
        textColor=BLANC, alignment=TA_CENTER
    )
    style_normal = ParagraphStyle(
        "normal", fontName="Helvetica", fontSize=9,
        textColor=NOIR, alignment=TA_LEFT
    )
    style_bold = ParagraphStyle(
        "bold", fontName="Helvetica-Bold", fontSize=9,
        textColor=NOIR, alignment=TA_LEFT
    )
    style_merci = ParagraphStyle(
        "merci", fontName="Helvetica-Oblique", fontSize=9,
        textColor=colors.grey, alignment=TA_CENTER
    )

    # ── EN-TÊTE ───────────────────────────────────────────────
    date_echeance = data.get("date_echeance", data["date"])

    entete_data = [
        [
            Paragraph(f"<b>{MON_NOM}</b>", style_titre),
            Paragraph("Merci de payer dans les délais.", style_merci),
            Paragraph(
                f"<b>Facture de Services</b><br/>"
                f"N: {data['numero']}<br/>"
                f"({datetime.now().strftime('%Y%m%d')})",
                style_normal
            ),
        ]
    ]
    entete_table = Table(entete_data, colWidths=[6*cm, 6*cm, 6*cm])
    entete_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLANC),
        ("BOX", (0, 0), (-1, -1), 1, VERT_ENEO),
        ("LINEAFTER", (0, 0), (1, 0), 0.5, VERT_CLAIR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(entete_table)
    story.append(Spacer(1, 0.3*cm))

    # Ligne "Thank you for paying on time"
    merci_data = [[
        Paragraph(f"Tél : {MON_TELEPHONE}", style_normal),
        Paragraph("Thank you for paying on time.", style_merci),
        Paragraph("", style_normal),
    ]]
    merci_table = Table(merci_data, colWidths=[6*cm, 6*cm, 6*cm])
    merci_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLAIR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(merci_table)
    story.append(Spacer(1, 0.3*cm))

    # ── INFO CLIENT + DATE ÉCHÉANCE ───────────────────────────
    date_box = Table(
        [[Paragraph(f"<b>{date_echeance}</b>", ParagraphStyle(
            "date", fontName="Helvetica-Bold", fontSize=14,
            textColor=BLANC, alignment=TA_CENTER
        ))]],
        colWidths=[5*cm], rowHeights=[1.5*cm]
    )
    date_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), JAUNE_DATE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 1, colors.orange),
    ]))

    client_data = [
        [
            Paragraph(
                f"<b>{data['client']}</b><br/>"
                f"Tél : {data.get('tel_client', 'N/A')}<br/>"
                f"Ville : Cameroun",
                style_normal
            ),
            Paragraph(
                f"N° Facture : {data['numero']}<br/>"
                f"Date : {data['date']}<br/>"
                f"Mode paiement : {data['mode_paiement']}",
                style_normal
            ),
            date_box,
        ]
    ]
    client_table = Table(client_data, colWidths=[6*cm, 7*cm, 5*cm])
    client_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, VERT_CLAIR),
        ("LINEAFTER", (0, 0), (1, 0), 0.5, VERT_CLAIR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLAIR),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 0.4*cm))

    # Catégorie
    cat_data = [[
        Paragraph("", style_normal),
        Paragraph("", style_normal),
        Paragraph(
            f"Catégorie / Category : SERVICES",
            ParagraphStyle("cat", fontName="Helvetica", fontSize=8,
                           textColor=colors.grey, alignment=TA_RIGHT)
        ),
    ]]
    cat_table = Table(cat_data, colWidths=[6*cm, 5*cm, 7*cm])
    story.append(cat_table)
    story.append(Spacer(1, 0.2*cm))

    # ── TABLEAU DES SERVICES ──────────────────────────────────
    header_style = ParagraphStyle(
        "header", fontName="Helvetica-Bold", fontSize=9,
        textColor=BLANC, alignment=TA_CENTER
    )
    cell_style = ParagraphStyle(
        "cell", fontName="Helvetica", fontSize=9,
        textColor=NOIR, alignment=TA_LEFT
    )
    cell_right = ParagraphStyle(
        "cell_r", fontName="Helvetica", fontSize=9,
        textColor=NOIR, alignment=TA_RIGHT
    )
    cell_bold_right = ParagraphStyle(
        "cell_br", fontName="Helvetica-Bold", fontSize=9,
        textColor=NOIR, alignment=TA_RIGHT
    )

    # En-têtes
    services_header = [
        Paragraph("Détails de la facture /<br/>Bill Items", header_style),
        Paragraph("Qté /<br/>Qty", header_style),
        Paragraph("Prix unitaire /<br/>Unit Price", header_style),
        Paragraph("MONTANT /<br/>AMOUNT", header_style),
    ]

    # Lignes de services
    services_rows = [services_header]
    total = 0
    for item in data.get("services", []):
        montant = item.get("quantite", 1) * item.get("prix_unitaire", 0)
        total += montant
        services_rows.append([
            Paragraph(item.get("description", ""), cell_style),
            Paragraph(str(item.get("quantite", 1)), cell_style),
            Paragraph(f"{item.get('prix_unitaire', 0):,.0f}", cell_right),
            Paragraph(f"{montant:,.0f}", cell_right),
        ])

    # Ligne total HT
    services_rows.append([
        Paragraph("TOTAL Hors Taxes / TOTAL Without Tax", cell_style),
        Paragraph("", cell_style),
        Paragraph("", cell_right),
        Paragraph(f"{total:,.0f}", cell_bold_right),
    ])

    # Ligne TVA (19.25%)
    tva = total * 0.1925
    services_rows.append([
        Paragraph("TVA / VAT (19.25%)", cell_style),
        Paragraph("", cell_style),
        Paragraph("", cell_right),
        Paragraph(f"{tva:,.0f}", cell_right),
    ])

    # Ligne TOTAL TTC
    ttc = total + tva
    services_rows.append([
        Paragraph("<b>TOTAL TTC / WITH TAX</b>", ParagraphStyle(
            "ttc", fontName="Helvetica-Bold", fontSize=10,
            textColor=VERT_HEADER, alignment=TA_LEFT
        )),
        Paragraph("", cell_style),
        Paragraph("", cell_right),
        Paragraph(f"<b>{ttc:,.0f} {DEVISE}</b>", ParagraphStyle(
            "ttc_r", fontName="Helvetica-Bold", fontSize=11,
            textColor=VERT_HEADER, alignment=TA_RIGHT
        )),
    ])

    services_table = Table(
        services_rows,
        colWidths=[9*cm, 2*cm, 3.5*cm, 3.5*cm]
    )
    n_rows = len(services_rows)
    services_table.setStyle(TableStyle([
        # En-tête vert
        ("BACKGROUND", (0, 0), (-1, 0), VERT_ENEO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANC),
        # Lignes alternées
        ("ROWBACKGROUNDS", (0, 1), (-1, n_rows-3), [BLANC, GRIS_CLAIR]),
        # Ligne total HT
        ("BACKGROUND", (0, n_rows-3), (-1, n_rows-3), VERT_CLAIR),
        # Ligne TVA
        ("BACKGROUND", (0, n_rows-2), (-1, n_rows-2), GRIS_CLAIR),
        # Ligne TTC
        ("BACKGROUND", (0, n_rows-1), (-1, n_rows-1), colors.HexColor("#E8F5E9")),
        ("LINEABOVE", (0, n_rows-1), (-1, n_rows-1), 1.5, VERT_ENEO),
        # Bordures
        ("GRID", (0, 0), (-1, -1), 0.5, VERT_CLAIR),
        ("BOX", (0, 0), (-1, -1), 1, VERT_ENEO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(services_table)
    story.append(Spacer(1, 0.5*cm))

    # ── RÉSUMÉ PAIEMENT ───────────────────────────────────────
    resume_data = [
        [
            Paragraph("<b>Total Facture</b>", style_bold),
            Paragraph(f"<b>{ttc:,.0f} {DEVISE}</b>", ParagraphStyle(
                "res_r", fontName="Helvetica-Bold", fontSize=10,
                textColor=VERT_HEADER, alignment=TA_RIGHT
            )),
        ],
        [
            Paragraph("Montant payé / Amount Paid", style_normal),
            Paragraph(f"{data.get('montant_paye', ttc):,.0f} {DEVISE}", ParagraphStyle(
                "res_r2", fontName="Helvetica", fontSize=9,
                textColor=NOIR, alignment=TA_RIGHT
            )),
        ],
    ]
    resume_table = Table(resume_data, colWidths=[9*cm, 9*cm])
    resume_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F5E9")),
        ("BACKGROUND", (0, 1), (-1, 1), GRIS_CLAIR),
        ("BOX", (0, 0), (-1, -1), 1, VERT_ENEO),
        ("GRID", (0, 0), (-1, -1), 0.5, VERT_CLAIR),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(resume_table)
    story.append(Spacer(1, 0.5*cm))

    # ── MESSAGE CLIENT ────────────────────────────────────────
    msg_data = [[
        Paragraph(
            f"<b>MESSAGE AU CLIENT :</b> "
            f"Merci de votre confiance ! Pour tout paiement :<br/>"
            f"MTN MoMo : {MTN_NUMERO} | Orange Money : {OM_NUMERO} | Wave : {WAVE_NUMERO}",
            ParagraphStyle("msg", fontName="Helvetica", fontSize=8,
                           textColor=VERT_HEADER, alignment=TA_LEFT)
        )
    ]]
    msg_table = Table(msg_data, colWidths=[18*cm])
    msg_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E8F5E9")),
        ("BOX", (0, 0), (-1, -1), 1, VERT_ENEO),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(msg_table)
    story.append(Spacer(1, 0.4*cm))

    # ── SIGNATURE ─────────────────────────────────────────────
    sig_data = [[
        Paragraph("", style_normal),
        Paragraph(
            f"<b>Cachet et Signature</b><br/><br/><br/><br/>"
            f"<b>{MON_NOM}</b><br/>{MON_TELEPHONE}",
            ParagraphStyle("sig", fontName="Helvetica", fontSize=9,
                           textColor=NOIR, alignment=TA_CENTER)
        ),
    ]]
    sig_table = Table(sig_data, colWidths=[10*cm, 8*cm])
    sig_table.setStyle(TableStyle([
        ("BOX", (1, 0), (1, 0), 1, VERT_ENEO),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(sig_table)

    # ── PIED DE PAGE ──────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    footer_line = Table(
        [[Paragraph(
            f"<i>{MON_NOM} — Facture générée automatiquement le {data['date']} — "
            f"Document non modifiable</i>",
            ParagraphStyle("footer", fontName="Helvetica-Oblique", fontSize=7,
                           textColor=colors.grey, alignment=TA_CENTER)
        )]],
        colWidths=[18*cm]
    )
    footer_line.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, -1), 1, VERT_ENEO),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(footer_line)

    doc.build(story)
    return filename


# ============================================================
# HANDLERS DU BOT
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📄 Nouvelle Facture", callback_data="nouvelle_facture")],
        [InlineKeyboardButton("📊 Historique", callback_data="historique")],
        [InlineKeyboardButton("ℹ️ Aide", callback_data="aide")],
    ]
    await update.message.reply_text(
        f"👋 Bienvenue sur *{MON_NOM}* !\n\n"
        "Je génère vos factures professionnelles automatiquement.\n\n"
        "Choisissez une option :",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return MENU_PRINCIPAL


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "nouvelle_facture":
        await query.message.reply_text(
            "👤 *Étape 1/4 — Nom du client*\n\n"
            "Entrez le nom complet du client :",
            parse_mode="Markdown"
        )
        return SAISIE_CLIENT

    elif query.data == "historique":
        transactions = charger_transactions()
        if not transactions:
            await query.message.reply_text("📭 Aucune transaction enregistrée.")
        else:
            msg = "📊 *Historique des factures :*\n\n"
            for t in transactions[-10:]:
                msg += f"• `{t['numero']}` — {t['client']} — *{t.get('total_ttc', 0):,.0f} FCFA* — {t['date']}\n"
            await query.message.reply_text(msg, parse_mode="Markdown")
        return MENU_PRINCIPAL

    elif query.data == "aide":
        await query.message.reply_text(
            "ℹ️ *Comment utiliser le bot :*\n\n"
            "1. Cliquez sur *Nouvelle Facture*\n"
            "2. Entrez le nom du client\n"
            "3. Décrivez le(s) service(s)\n"
            "4. Entrez le montant\n"
            "5. Choisissez le mode de paiement\n"
            "6. La facture PDF est générée automatiquement !\n\n"
            f"📞 Support : {MON_TELEPHONE}",
            parse_mode="Markdown"
        )
        return MENU_PRINCIPAL


async def saisie_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["client"] = update.message.text.strip()
    await update.message.reply_text(
        "🛍️ *Étape 2/4 — Services*\n\n"
        "Décrivez le(s) service(s) avec quantité et prix unitaire.\n\n"
        "Format : `Description, quantité, prix unitaire`\n"
        "Exemple : `Recharge MTN, 1, 5000`\n\n"
        "Envoyez plusieurs lignes pour plusieurs services.\n"
        "Tapez *DONE* quand vous avez terminé.",
        parse_mode="Markdown"
    )
    context.user_data["services"] = []
    return SAISIE_SERVICE


async def saisie_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.upper() == "DONE":
        if not context.user_data["services"]:
            await update.message.reply_text("⚠️ Ajoutez au moins un service avant de continuer.")
            return SAISIE_SERVICE
        await update.message.reply_text(
            "💰 *Étape 3/4 — Mode de paiement*\n\n"
            "Choisissez le mode de paiement :",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 MTN Mobile Money", callback_data="pay_mtn")],
                [InlineKeyboardButton("🟠 Orange Money", callback_data="pay_om")],
                [InlineKeyboardButton("🌊 Wave", callback_data="pay_wave")],
                [InlineKeyboardButton("💵 Espèces", callback_data="pay_cash")],
            ]),
            parse_mode="Markdown"
        )
        return SAISIE_PAIEMENT

    # Parser la ligne
    parts = [p.strip() for p in text.split(",")]
    if len(parts) < 3:
        await update.message.reply_text(
            "⚠️ Format incorrect.\n"
            "Utilisez : `Description, quantité, prix unitaire`\n"
            "Exemple : `Recharge MTN, 1, 5000`",
            parse_mode="Markdown"
        )
        return SAISIE_SERVICE

    try:
        description = parts[0]
        quantite = int(parts[1])
        prix = float(parts[2].replace(" ", "").replace("FCFA", ""))
        context.user_data["services"].append({
            "description": description,
            "quantite": quantite,
            "prix_unitaire": prix
        })
        total_partiel = sum(s["quantite"] * s["prix_unitaire"] for s in context.user_data["services"])
        await update.message.reply_text(
            f"✅ Service ajouté : *{description}* — {quantite} x {prix:,.0f} FCFA\n"
            f"Sous-total : *{total_partiel:,.0f} FCFA*\n\n"
            "Ajoutez un autre service ou tapez *DONE* pour continuer.",
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text(
            "⚠️ Quantité ou prix invalide. Réessayez.",
            parse_mode="Markdown"
        )

    return SAISIE_SERVICE


async def saisie_paiement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    modes = {
        "pay_mtn": f"MTN Mobile Money ({MTN_NUMERO})",
        "pay_om": f"Orange Money ({OM_NUMERO})",
        "pay_wave": f"Wave ({WAVE_NUMERO})",
        "pay_cash": "Espèces"
    }
    context.user_data["mode_paiement"] = modes.get(query.data, "Non spécifié")

    # Calcul totaux
    services = context.user_data["services"]
    total_ht = sum(s["quantite"] * s["prix_unitaire"] for s in services)
    tva = total_ht * 0.1925
    ttc = total_ht + tva

    # Résumé
    resume = f"📋 *Résumé de la facture :*\n\n"
    resume += f"👤 Client : *{context.user_data['client']}*\n"
    resume += f"💳 Paiement : {context.user_data['mode_paiement']}\n\n"
    resume += "🛍️ *Services :*\n"
    for s in services:
        resume += f"  • {s['description']} ({s['quantite']} x {s['prix_unitaire']:,.0f}) = *{s['quantite']*s['prix_unitaire']:,.0f} FCFA*\n"
    resume += f"\n💰 Total HT : {total_ht:,.0f} FCFA\n"
    resume += f"📊 TVA (19.25%) : {tva:,.0f} FCFA\n"
    resume += f"✅ *TOTAL TTC : {ttc:,.0f} FCFA*\n\n"
    resume += "Confirmez-vous la génération de la facture ?"

    context.user_data["total_ttc"] = ttc

    await query.message.reply_text(
        resume,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Confirmer", callback_data="confirmer"),
                InlineKeyboardButton("❌ Annuler", callback_data="annuler"),
            ]
        ]),
        parse_mode="Markdown"
    )
    return CONFIRMATION


async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "annuler":
        await query.message.reply_text("❌ Facture annulée. Tapez /start pour recommencer.")
        return ConversationHandler.END

    # Générer la facture
    numero = generer_numero_facture()
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y à %H:%M")

    services = context.user_data["services"]
    total_ht = sum(s["quantite"] * s["prix_unitaire"] for s in services)
    ttc = total_ht * 1.1925

    data = {
        "numero": numero,
        "client": context.user_data["client"],
        "date": date_str,
        "date_echeance": now.strftime("%d/%m/%Y"),
        "services": services,
        "mode_paiement": context.user_data["mode_paiement"],
        "montant_paye": ttc,
        "total_ttc": ttc,
    }

    await query.message.reply_text("⏳ Génération de la facture en cours...")

    try:
        pdf_path = generer_facture_pdf(data)
        sauvegarder_transaction(data)

        with open(pdf_path, "rb") as pdf_file:
            await query.message.reply_document(
                document=pdf_file,
                filename=f"Facture_{numero}.pdf",
                caption=(
                    f"✅ *Facture générée avec succès !*\n\n"
                    f"📄 N° : `{numero}`\n"
                    f"👤 Client : {data['client']}\n"
                    f"💰 Total TTC : *{ttc:,.0f} FCFA*\n"
                    f"💳 Paiement : {data['mode_paiement']}\n"
                    f"📅 Date : {date_str}"
                ),
                parse_mode="Markdown"
            )

        # Nettoyage du fichier temporaire
        os.remove(pdf_path)

    except Exception as e:
        logger.error(f"Erreur génération PDF : {e}")
        await query.message.reply_text(
            f"❌ Erreur lors de la génération : {str(e)}\n"
            "Contactez le support."
        )

    keyboard = [[InlineKeyboardButton("🏠 Menu principal", callback_data="menu")]]
    await query.message.reply_text(
        "Que souhaitez-vous faire ?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Nouvelle Facture", callback_data="nouvelle_facture")],
            [InlineKeyboardButton("📊 Historique", callback_data="historique")],
        ])
    )
    return MENU_PRINCIPAL


async def annuler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Opération annulée. Tapez /start pour recommencer.")
    return ConversationHandler.END


# ============================================================
# LANCEMENT DU BOT
# ============================================================
def main():
    if not TOKEN:
        logger.error("❌ BOT_TOKEN manquant ! Ajoutez-le dans les variables Railway.")
        return
lancement du serveur web en arriere-plan
Thread(target=run_flask).start()
logger.info("serveur web de secours démarré (port 10000)")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU_PRINCIPAL: [CallbackQueryHandler(menu_callback)],
            SAISIE_CLIENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, saisie_client)],
            SAISIE_SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, saisie_service),
                CallbackQueryHandler(saisie_paiement, pattern="^pay_"),
            ],
            SAISIE_PAIEMENT: [CallbackQueryHandler(saisie_paiement, pattern="^pay_")],
            CONFIRMATION: [CallbackQueryHandler(confirmation)],
        },
        fallbacks=[CommandHandler("annuler", annuler)],
    )

    app.add_handler(conv_handler)

    logger.info(f"✅ {MON_NOM} — Bot démarré avec succès !")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
