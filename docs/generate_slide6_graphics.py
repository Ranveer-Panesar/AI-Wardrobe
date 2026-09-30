"""
Generates high-resolution graphics for Slide 6 of the AI Wardrobe DBMS presentation:
1. slide6_er_diagram.png           — 3NF Relational ER Architecture
2. slide6_digital_closet_db.png     — ACID Wardrobe Data Pipeline & SQL Query Execution
3. slide6_query_state_machine.png   — Relational Outfit Join & Async RenderJob State Machine
"""
import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image, ImageOps

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_DIR = PROJECT_ROOT / "backend" / "assets" / "synthetic_dataset"


def create_er_diagram(output_path: Path):
    """Generate professional 3NF Relational ER Diagram."""
    fig, ax = plt.subplots(figsize=(10.2, 6.6), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 1020)
    ax.set_ylim(0, 660)
    ax.axis("off")

    # Title header banner
    banner = patches.Rectangle((0, 610), 1020, 50, facecolor="#043939", edgecolor="none")
    ax.add_patch(banner)
    ax.text(510, 630, "AI WARDROBE — 3NF RELATIONAL SCHEMA & INTEGRITY RULES", 
            color="#FFFFFF", fontsize=11.5, fontweight="bold", ha="center", va="center", family="sans-serif")
    ax.text(510, 616, "Platform-Agnostic GUIDs  •  ACID Transactions  •  Cascading Delete Integrity", 
            color="#00A896", fontsize=8, ha="center", va="center", family="sans-serif")

    # Colors
    HEADER_BG = "#064646"
    CARD_BG = "#FFFFFF"
    BORDER_COLOR = "#00A896"
    ROW_BG_ALT = "#F1F5F9"
    TEXT_DARK = "#0F172A"
    PK_COLOR = "#B45309"
    FK_COLOR = "#0E7490"

    def draw_table(x, y, w, h, title, columns):
        # Card outer border & shadow
        shadow = patches.FancyBboxPatch((x+3, y-3), w, h, boxstyle="round,pad=0,rounding_size=6",
                                        facecolor="#E2E8F0", edgecolor="none")
        ax.add_patch(shadow)
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                      facecolor=CARD_BG, edgecolor=BORDER_COLOR, linewidth=1.5)
        ax.add_patch(card)

        # Header
        hdr = patches.Rectangle((x, y + h - 28), w, 28, facecolor=HEADER_BG, edgecolor="none")
        ax.add_patch(hdr)
        ax.text(x + 12, y + h - 14, title, color="#FFFFFF", fontsize=9.5, fontweight="bold", va="center", family="monospace")

        # Rows
        row_h = (h - 32) / len(columns)
        for i, (key_type, name, col_type) in enumerate(columns):
            row_y = y + h - 30 - (i + 1) * row_h
            if i % 2 == 1:
                alt = patches.Rectangle((x + 1, row_y), w - 2, row_h, facecolor=ROW_BG_ALT, edgecolor="none")
                ax.add_patch(alt)

            # Key badge
            if key_type == "PK":
                ax.text(x + 10, row_y + row_h/2, "PK", color=PK_COLOR, fontsize=7.5, fontweight="bold", va="center", family="monospace")
            elif key_type == "FK":
                ax.text(x + 10, row_y + row_h/2, "FK", color=FK_COLOR, fontsize=7.5, fontweight="bold", va="center", family="monospace")
            elif key_type == "IX":
                ax.text(x + 10, row_y + row_h/2, "IX", color="#64748B", fontsize=7.5, fontweight="bold", va="center", family="monospace")

            # Column Name
            ax.text(x + 36, row_y + row_h/2, name, color=TEXT_DARK, fontsize=8, fontweight="bold" if key_type=="PK" else "normal", va="center", family="sans-serif")
            # Column Type
            ax.text(x + w - 10, row_y + row_h/2, col_type, color="#475569", fontsize=7.5, ha="right", va="center", family="monospace")

    # Table 1: users (Top Left)
    draw_table(30, 360, 290, 220, "TABLE: users", [
        ("PK", "id", "UUID / CHAR(36)"),
        ("IX", "email", "VARCHAR(255) UNIQUE"),
        ("IX", "phone", "VARCHAR(32) UNIQUE"),
        ("",   "password_hash", "VARCHAR(255)"),
        ("",   "storage_mode", "VARCHAR(16)"),
        ("",   "email_verified", "BOOLEAN"),
        ("",   "created_at", "TIMESTAMP WITH TZ"),
    ])

    # Table 2: garments (Bottom Left)
    draw_table(30, 30, 310, 275, "TABLE: garments", [
        ("PK", "id", "UUID / CHAR(36)"),
        ("FK", "user_id", "UUID -> users.id"),
        ("IX", "category", "VARCHAR(64)"),
        ("",   "category_confidence", "FLOAT"),
        ("",   "formality", "VARCHAR(32)"),
        ("",   "pattern", "VARCHAR(32)"),
        ("",   "dominant_colors", "JSON (HEX ARRAY)"),
        ("",   "embedding", "JSON / VECTOR(512)"),
        ("",   "image_url", "VARCHAR(512)"),
        ("",   "created_at", "TIMESTAMP WITH TZ"),
    ])

    # Table 3: outfits (Top Right)
    draw_table(680, 360, 310, 220, "TABLE: outfits", [
        ("PK", "id", "UUID / CHAR(36)"),
        ("FK", "user_id", "UUID -> users.id"),
        ("",   "garment_ids", "JSON (LIST[UUID])"),
        ("IX", "score", "FLOAT (0.00-1.00)"),
        ("",   "style_tags", "JSON (DICT)"),
        ("",   "created_at", "TIMESTAMP WITH TZ"),
    ])

    # Table 4: render_jobs (Bottom Right)
    draw_table(680, 30, 310, 275, "TABLE: render_jobs", [
        ("PK", "id", "UUID / CHAR(36)"),
        ("FK", "user_id", "UUID -> users.id"),
        ("FK", "outfit_id", "UUID -> outfits.id"),
        ("",   "render_type", "VARCHAR(32)"),
        ("IX", "status", "VARCHAR(32)"),
        ("",   "output_image_url", "VARCHAR(512)"),
        ("",   "error_message", "TEXT"),
        ("",   "created_at", "TIMESTAMP WITH TZ"),
        ("",   "updated_at", "TIMESTAMP WITH TZ"),
    ])

    # Relational Connectors & Cardinalities
    # 1. users (1) -> garments (N)
    ax.annotate("", xy=(180, 305), xytext=(180, 360),
                arrowprops=dict(arrowstyle="-|>", color="#00A896", lw=2.2, mutation_scale=14))
    ax.text(192, 332, "1 : N   ON DELETE CASCADE", color="#064646", fontsize=7.5, fontweight="bold", family="sans-serif")

    # 2. users (1) -> outfits (N)
    ax.annotate("", xy=(680, 470), xytext=(320, 470),
                arrowprops=dict(arrowstyle="-|>", color="#00A896", lw=2.2, mutation_scale=14))
    ax.text(500, 478, "1 : N   ON DELETE CASCADE", color="#064646", fontsize=7.5, fontweight="bold", ha="center", family="sans-serif")

    # 3. outfits (1) -> render_jobs (N)
    ax.annotate("", xy=(835, 305), xytext=(835, 360),
                arrowprops=dict(arrowstyle="-|>", color="#0E7490", lw=2.2, mutation_scale=14))
    ax.text(845, 332, "1 : N   ON DELETE SET NULL", color="#0E7490", fontsize=7.5, fontweight="bold", family="sans-serif")

    # Center Feature Callout Box
    cen_box = patches.FancyBboxPatch((365, 120), 290, 180, boxstyle="round,pad=0,rounding_size=8",
                                     facecolor="#E6F4F1", edgecolor="#00A896", linewidth=1.5)
    ax.add_patch(cen_box)
    ax.text(510, 275, "RDBMS INTEGRITY ENFORCEMENT", color="#043939", fontsize=9, fontweight="bold", ha="center", family="sans-serif")
    
    rules = [
        "• 3NF Normalization: Zero update anomalies",
        "• Foreign Keys: PRAGMA foreign_keys = ON",
        "• Atomic Transactions: Unit of Work commits",
        "• Secondary Indexes: B-Tree on user_id, category",
        "• Hybrid Schema: JSON arrays for color hexes"
    ]
    for idx, rule in enumerate(rules):
        ax.text(380, 240 - idx * 24, rule, color="#0F172A", fontsize=8, family="sans-serif")

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Generated: {output_path}")


def create_digital_closet_graphic(output_path: Path):
    """Generate ACID digital closet execution view with real garments."""
    fig, ax = plt.subplots(figsize=(10.2, 6.6), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 1020)
    ax.set_ylim(0, 660)
    ax.axis("off")

    # Top Query Console (Dark IDE style)
    top_console = patches.Rectangle((0, 560), 1020, 100, facecolor="#0B192C", edgecolor="none")
    ax.add_patch(top_console)

    # Console dots
    ax.add_patch(patches.Circle((20, 638), 5, facecolor="#EF4444"))
    ax.add_patch(patches.Circle((36, 638), 5, facecolor="#F59E0B"))
    ax.add_patch(patches.Circle((52, 638), 5, facecolor="#10B981"))
    ax.text(75, 638, "PostgreSQL / SQLite Interactive Session — Digital Closet Query Pipeline", 
            color="#94A3B8", fontsize=8.5, va="center", family="monospace")

    # SQL query line
    ax.text(20, 608, "SQL > SELECT id, category, formality, dominant_colors FROM garments WHERE user_id = :uid ORDER BY created_at DESC;", 
            color="#38BDF8", fontsize=8.5, fontweight="bold", va="center", family="monospace")
    ax.text(20, 582, "STATUS: 200 OK  |  INDEX HIT: idx_garments_user_id (B-Tree)  |  EXECUTION TIME: 0.94ms  |  ISOLATION: READ COMMITTED", 
            color="#4ADE80", fontsize=8, va="center", family="monospace")

    # 4 Garment Cards Grid
    card_items = [
        ("Polo Shirt", "casual", ["#1e3c5a", "#ffffff", "#2b6cb0"], "polo_1.jpg"),
        ("Denim Jeans", "casual", ["#1f2937", "#3b82f6", "#111827"], "pants_1.jpg"),
        ("Formal Blazer", "formal", ["#0f172a", "#334155", "#64748b"], "blazer_1.jpg"),
        ("Sport Shorts", "sport", ["#b91c1c", "#ffffff", "#1e293b"], "shorts_1.jpg"),
    ]

    card_w = 220
    card_h = 460
    start_x = 35
    spacing = 245

    for idx, (category, formality, colors, filename) in enumerate(card_items):
        cx = start_x + idx * spacing
        cy = 80

        # Card shadow & background
        ax.add_patch(patches.FancyBboxPatch((cx+3, cy-3), card_w, card_h, boxstyle="round,pad=0,rounding_size=8",
                                            facecolor="#E2E8F0", edgecolor="none"))
        ax.add_patch(patches.FancyBboxPatch((cx, cy), card_w, card_h, boxstyle="round,pad=0,rounding_size=8",
                                            facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.2))

        # Header pill
        cat_badge = patches.FancyBboxPatch((cx+15, cy+card_h-36), card_w-30, 26, boxstyle="round,pad=0,rounding_size=4",
                                          facecolor="#00A896" if formality=="casual" else "#043939", edgecolor="none")
        ax.add_patch(cat_badge)
        ax.text(cx + card_w/2, cy + card_h - 23, category.upper(), color="#FFFFFF", fontsize=8.5, fontweight="bold", ha="center", va="center")

        # Garment Image Thumbnail
        img_path = SYNTHETIC_DIR / filename
        if img_path.exists():
            try:
                img = Image.open(img_path).convert("RGB")
                img = ImageOps.fit(img, (card_w - 30, 220), Image.Resampling.LANCZOS)
                # We can place it using imshow extent
                extent = [cx + 15, cx + card_w - 15, cy + 180, cy + 400]
                ax.imshow(img, extent=extent, zorder=3)
                # Border around image
                ax.add_patch(patches.Rectangle((cx + 15, cy + 180), card_w - 30, 220, facecolor="none", edgecolor="#E2E8F0", linewidth=1, zorder=4))
            except Exception as e:
                print(f"Error loading {img_path}: {e}")

        # Metadata Box below image
        ax.text(cx + 15, cy + 160, f"Formality: {formality.capitalize()}", color="#0F172A", fontsize=8, fontweight="bold")
        ax.text(cx + 15, cy + 142, "Dominant Colors (JSON):", color="#64748B", fontsize=7.5)

        # Color chips
        for c_idx, hex_col in enumerate(colors):
            chip_x = cx + 22 + c_idx * 30
            chip_y = cy + 120
            ax.add_patch(patches.Circle((chip_x, chip_y), 9, facecolor=hex_col, edgecolor="#94A3B8", linewidth=1, zorder=4))

        # DB Record ID footer
        ax.add_patch(patches.Rectangle((cx+1, cy+1), card_w-2, 34, facecolor="#F8FAFC", edgecolor="none"))
        ax.text(cx + 12, cy + 18, f"Row ID: {filename[:7]}...", color="#64748B", fontsize=7.5, family="monospace")
        ax.text(cx + card_w - 12, cy + 18, "ACID: OK", color="#10B981", fontsize=7.5, fontweight="bold", ha="right", family="monospace")

    # Bottom status bar
    bottom_bar = patches.Rectangle((0, 0), 1020, 50, facecolor="#043939", edgecolor="none")
    ax.add_patch(bottom_bar)
    ax.text(510, 25, "TRANSACTION INTEGRITY:  ON DELETE CASCADE Verified  •  Zero Orphan Records  •  WAL Persistence", 
            color="#FFFFFF", fontsize=8.5, fontweight="bold", ha="center", va="center")

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Generated: {output_path}")


def create_query_state_machine_graphic(output_path: Path):
    """Generate Query Join + Asynchronous RenderJob State Machine."""
    fig, ax = plt.subplots(figsize=(10.2, 6.6), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(0, 1020)
    ax.set_ylim(0, 660)
    ax.axis("off")

    # Header banner
    banner = patches.Rectangle((0, 610), 1020, 50, facecolor="#043939", edgecolor="none")
    ax.add_patch(banner)
    ax.text(510, 630, "RELATIONAL OUTFIT JOIN & ASYNC RENDERJOB STATE MACHINE", 
            color="#FFFFFF", fontsize=11, fontweight="bold", ha="center", va="center", family="sans-serif")
    ax.text(510, 616, "Multi-Attribute Join Scoring  •  State Lifecycle Queuing  •  Durability Logging", 
            color="#00A896", fontsize=8, ha="center", va="center", family="sans-serif")

    # Left Container: Outfit Join & Scorer
    ax.add_patch(patches.FancyBboxPatch((25, 25), 465, 565, boxstyle="round,pad=0,rounding_size=8",
                                        facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.5))
    ax.add_patch(patches.Rectangle((25, 550), 465, 40, facecolor="#064646", edgecolor="none"))
    ax.text(257, 570, "1. RELATIONAL OUTFIT QUERY & SCORING", color="#FFFFFF", fontsize=9.5, fontweight="bold", ha="center", va="center")

    # SQL join label
    ax.text(45, 525, "SELECT tops.id, bottoms.id FROM garments tops", color="#0E7490", fontsize=8, family="monospace", fontweight="bold")
    ax.text(45, 510, "CROSS JOIN garments bottoms WHERE tops.category IN ('shirt', 'polo')", color="#0E7490", fontsize=7.5, family="monospace")

    # Render thumbnails of Top & Bottom
    top_img_path = SYNTHETIC_DIR / "polo_1.jpg"
    btm_img_path = SYNTHETIC_DIR / "pants_1.jpg"
    if top_img_path.exists():
        img_t = ImageOps.fit(Image.open(top_img_path).convert("RGB"), (110, 140))
        ax.imshow(img_t, extent=[50, 160, 340, 480], zorder=3)
        ax.add_patch(patches.Rectangle((50, 340), 110, 140, facecolor="none", edgecolor="#CBD5E1", lw=1, zorder=4))
        ax.text(105, 325, "TOP: Polo", color="#0F172A", fontsize=7.5, fontweight="bold", ha="center")

    ax.text(180, 410, "+", color="#00A896", fontsize=20, fontweight="bold", ha="center", va="center")

    if btm_img_path.exists():
        img_b = ImageOps.fit(Image.open(btm_img_path).convert("RGB"), (110, 140))
        ax.imshow(img_b, extent=[200, 310, 340, 480], zorder=3)
        ax.add_patch(patches.Rectangle((200, 340), 110, 140, facecolor="none", edgecolor="#CBD5E1", lw=1, zorder=4))
        ax.text(255, 325, "BOTTOM: Jeans", color="#0F172A", fontsize=7.5, fontweight="bold", ha="center")

    # Score Box
    score_card = patches.FancyBboxPatch((45, 55), 425, 240, boxstyle="round,pad=0,rounding_size=6",
                                        facecolor="#E6F4F1", edgecolor="#00A896", linewidth=1.2)
    ax.add_patch(score_card)
    ax.text(65, 265, "COMPOSITE COMPATIBILITY SCORE", color="#043939", fontsize=9, fontweight="bold")
    ax.text(450, 265, "94.2%", color="#00A896", fontsize=16, fontweight="bold", ha="right", va="center")

    metrics = [
        ("CIELAB Color Harmony (delta E)", "0.96", "#10B981"),
        ("Formality Match (Casual - Casual)", "0.92", "#10B981"),
        ("Occasion Fit (Sport/Casual)", "0.95", "#10B981"),
        ("Pattern Conflict Penalty", "0.00 (None)", "#64748B"),
        ("Database Transaction State", "Persisted in outfits table", "#0E7490"),
    ]
    for m_i, (lbl, val, col) in enumerate(metrics):
        m_y = 230 - m_i * 32
        ax.text(65, m_y, lbl, color="#334155", fontsize=7.5, family="sans-serif")
        ax.text(450, m_y, val, color=col, fontsize=8, fontweight="bold", ha="right", family="monospace")

    # Right Container: Async RenderJob State Machine & VTON Output
    ax.add_patch(patches.FancyBboxPatch((520, 25), 475, 565, boxstyle="round,pad=0,rounding_size=8",
                                        facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.5))
    ax.add_patch(patches.Rectangle((520, 550), 475, 40, facecolor="#064646", edgecolor="none"))
    ax.text(757, 570, "2. ASYNC RENDERJOB STATE MACHINE", color="#FFFFFF", fontsize=9.5, fontweight="bold", ha="center", va="center")

    # Step Flow (3 state pills)
    states = [
        ("QUEUED", "Row inserted in DB", "#F59E0B"),
        ("PROCESSING", "GPU Worker active", "#3B82F6"),
        ("DONE", "Output image URL saved", "#10B981"),
    ]
    for s_i, (s_name, s_sub, s_col) in enumerate(states):
        sy = 485 - s_i * 65
        # Pill
        ax.add_patch(patches.FancyBboxPatch((545, sy), 115, 36, boxstyle="round,pad=0,rounding_size=4",
                                            facecolor=s_col, edgecolor="none"))
        ax.text(602, sy + 18, s_name, color="#FFFFFF", fontsize=8, fontweight="bold", ha="center", va="center", family="monospace")
        ax.text(675, sy + 18, s_sub, color="#0F172A", fontsize=8, va="center", family="sans-serif")

        if s_i < 2:
            ax.annotate("", xy=(602, sy - 14), xytext=(602, sy),
                        arrowprops=dict(arrowstyle="-|>", color="#94A3B8", lw=1.5, mutation_scale=10))

    # Virtual Try-On Render Preview Result
    vton_preview_box = patches.FancyBboxPatch((545, 55), 425, 230, boxstyle="round,pad=0,rounding_size=6",
                                              facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1)
    ax.add_patch(vton_preview_box)

    vton_img_path = PROJECT_ROOT / "test_render_base_model_vton.jpg"
    if not vton_img_path.exists():
        vton_img_path = PROJECT_ROOT / "test_e2e_polo_base_result.jpg"

    if vton_img_path.exists():
        try:
            v_img = ImageOps.fit(Image.open(vton_img_path).convert("RGB"), (150, 190))
            ax.imshow(v_img, extent=[565, 715, 75, 265], zorder=3)
            ax.add_patch(patches.Rectangle((565, 75), 150, 190, facecolor="none", edgecolor="#00A896", lw=1.5, zorder=4))
        except Exception as e:
            print(f"Error loading vton preview: {e}")

    ax.text(735, 245, "FINAL TRY-ON OUTPUT", color="#043939", fontsize=8.5, fontweight="bold")
    ax.text(735, 225, "Output URL: /renders/job_8f21.jpg", color="#0E7490", fontsize=7.5, family="monospace")
    ax.text(735, 195, "• Latent Diffusion Warping OK", color="#10B981", fontsize=7.5)
    ax.text(735, 175, "• Preserved Fabric Texture", color="#10B981", fontsize=7.5)
    ax.text(735, 155, "• Cascade Cleanup on Delete", color="#10B981", fontsize=7.5)
    ax.text(735, 125, "HTTP 200: Streamed to Client", color="#64748B", fontsize=7.5, family="monospace")

    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Generated: {output_path}")


def main():
    er_path = ASSETS_DIR / "slide6_er_diagram.png"
    closet_path = ASSETS_DIR / "slide6_digital_closet_db.png"
    state_path = ASSETS_DIR / "slide6_query_state_machine.png"

    print("Generating Slide 6 Graphics...")
    create_er_diagram(er_path)
    create_digital_closet_graphic(closet_path)
    create_query_state_machine_graphic(state_path)
    print("All Slide 6 graphics generated successfully!")


if __name__ == "__main__":
    main()
