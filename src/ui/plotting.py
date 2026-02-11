
import matplotlib.patches as patches
import matplotlib.pyplot as plt


def draw_beam_section_flexure(b, h, cover, as_bot, as_top):
    fig, ax = plt.subplots(figsize=(4, 4))
    rect = patches.Rectangle((0, 0), b, h, linewidth=2, edgecolor='#333333', facecolor='#e0e0e0')
    ax.add_patch(rect)

    if as_bot > 0:
        ax.plot([cover, b-cover], [cover, cover], 'r-', linewidth=3, label='Bottom')
        ax.text(b/2, cover+2, f"As: {as_bot:.2f}", ha='center', color='red', fontsize=8)

    if as_top > 0:
        ax.plot([cover, b-cover], [h-cover, h-cover], 'b-', linewidth=3, label='Top')
        ax.text(b/2, h-cover-4, f"As: {as_top:.2f}", ha='center', color='blue', fontsize=8)

    ax.set_xlim(-5, b+5)
    ax.set_ylim(-5, h+5)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig


def draw_beam_section_shear(b, h, cover, s_req, n_legs):
    """Draw cross section with stirrup legs and side elevation with spacing."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 4), gridspec_kw={'width_ratios': [1, 1.2]})

    # --- Cross section ---
    rect = patches.Rectangle((0, 0), b, h, linewidth=2, edgecolor='#333333', facecolor='#e0e0e0')
    ax1.add_patch(rect)

    # Stirrup outline (dashed green)
    stirrup = patches.Rectangle(
        (cover, cover), b - 2*cover, h - 2*cover,
        linewidth=2, edgecolor='#2e7d32', facecolor='none', linestyle='--'
    )
    ax1.add_patch(stirrup)

    # Internal legs if n_legs > 2
    if n_legs > 2:
        inner_width = b - 2 * cover
        for i in range(1, n_legs - 1):
            x = cover + inner_width * i / (n_legs - 1)
            ax1.plot([x, x], [cover, h - cover], color='#2e7d32', linewidth=1.5, linestyle='--')

    ax1.set_xlim(-3, b + 3)
    ax1.set_ylim(-3, h + 3)
    ax1.set_aspect('equal')
    ax1.set_title("Seccion", fontsize=9)
    ax1.axis('off')

    # --- Side elevation with stirrup spacing ---
    beam_length = max(h * 1.5, 40)
    ax2.add_patch(patches.Rectangle((0, 0), beam_length, h, linewidth=2,
                                     edgecolor='#333333', facecolor='#f5f5f5'))

    if s_req and s_req > 0:
        x = cover
        while x < beam_length - cover:
            ax2.plot([x, x], [cover, h - cover], color='#2e7d32', linewidth=1.2)
            x += s_req
        ax2.set_title(f"Elevacion (s = {s_req:.1f} cm)", fontsize=9)
    else:
        ax2.set_title("Elevacion (sin estribos req.)", fontsize=9)

    ax2.set_xlim(-3, beam_length + 3)
    ax2.set_ylim(-3, h + 3)
    ax2.set_aspect('equal')
    ax2.axis('off')

    fig.tight_layout()
    return fig


def draw_beam_section_torsion(b, h, cover, al_total, n_long_bars=6):
    """Draw cross section with closed stirrups and longitudinal bars distributed on perimeter."""
    fig, ax = plt.subplots(figsize=(2.5, 3))

    # Outer section
    rect = patches.Rectangle((0, 0), b, h, linewidth=1.5, edgecolor='#333333', facecolor='#e0e0e0')
    ax.add_patch(rect)

    # Closed stirrup
    stirrup = patches.Rectangle(
        (cover, cover), b - 2*cover, h - 2*cover,
        linewidth=2, edgecolor='#7b1fa2', facecolor='none'
    )
    ax.add_patch(stirrup)

    # Distribute longitudinal bars on perimeter
    positions = _distribute_bars_on_perimeter(b, h, cover, n_long_bars)
    for (x, y) in positions:
        ax.plot(x, y, 'ro', markersize=5, markeredgecolor='darkred', markerfacecolor='red')

    # Label
    if al_total > 0:
        ax.text(b / 2, -3, f"Al: {al_total:.2f} cm2", ha='center', fontsize=7, color='darkred')

    ax.set_xlim(-4, b + 4)
    ax.set_ylim(-5, h + 4)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.tight_layout()
    return fig


def _distribute_bars_on_perimeter(b, h, cover, n_bars):
    """Distribute n_bars around the inner perimeter (at stirrup corners and edges)."""
    x_min, x_max = cover, b - cover
    y_min, y_max = cover, h - cover

    if n_bars <= 4:
        # Just corners
        return [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)][:n_bars]

    positions = []
    # Always place 4 corners first
    positions.append((x_min, y_min))
    positions.append((x_max, y_min))
    positions.append((x_max, y_max))
    positions.append((x_min, y_max))

    remaining = n_bars - 4
    if remaining <= 0:
        return positions

    # Distribute remaining bars along longer sides (bottom and top preferred)
    # Split evenly: bottom, top, left side, right side
    n_bottom = max(1, remaining // 2)
    n_top = remaining - n_bottom

    for i in range(1, n_bottom + 1):
        x = x_min + (x_max - x_min) * i / (n_bottom + 1)
        positions.append((x, y_min))

    for i in range(1, n_top + 1):
        x = x_min + (x_max - x_min) * i / (n_top + 1)
        positions.append((x, y_max))

    return positions
