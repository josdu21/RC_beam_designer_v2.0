import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

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
