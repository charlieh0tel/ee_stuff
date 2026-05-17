#!/usr/bin/env python3

"""
Generate regime-boundary figure for diode small-signal note.
Fully configured for native LaTeX integration.
"""

import matplotlib.pyplot as plt
import numpy as np

# Updated rcParams for native LaTeX rendering
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "text.usetex": True,
        "font.size": 10,
        "axes.labelsize": 11,
    }
)

# Si PN signal diode (1N4148-like) parameters
n = 1.85
VT = 0.0259
IS = 1.0e-9
VQ = 0.55
IQ = IS * np.exp(VQ / (n * VT))  # ~100 uA by construction

v_lin = 0.04 * n * VT  # ~ 1.9 mV
v_quad = n * VT  # ~ 48 mV
v_interm = VQ - 4 * VT  # ~ 446 mV

V = np.linspace(-0.15, 0.85, 1500)
I = IS * (np.exp(V / (n * VT)) - 1)  # noqa: E741
I_abs = np.maximum(np.abs(I), 1e-15)

fig = plt.figure(figsize=(6.8, 6.2))
gs = fig.add_gridspec(2, 1, height_ratios=[1.7, 1.0], hspace=0.45)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# ---------- Panel (a): I-V curve ----------
ax1.semilogy(
    V, I_abs, color="#1f4e79", linewidth=1.6, label=r"$I_D = I_S(e^{V_D/nV_T} - 1)$"
)

# Q-point
ax1.plot(VQ, IQ, "o", color="#c0392b", markersize=7, zorder=5)
ax1.annotate(
    r"Q: $V_Q=0.55$ V, $I_Q\approx 100\ \mu$A",
    xy=(VQ, IQ),
    xytext=(VQ - 0.45, IQ * 200),
    arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.8),
    fontsize=9,
    color="#c0392b",
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c0392b", alpha=0.95, lw=0.6),
)

# 4VT boundary
ax1.axvline(4 * VT, color="gray", linestyle=":", linewidth=0.9)
ax1.text(
    4 * VT + 0.008,
    1e-13,
    r"$4V_T\approx 104$ mV",
    fontsize=8,
    color="gray",
    ha="left",
    va="bottom",
)
ax1.axvline(VQ, color="#c0392b", linestyle="--", linewidth=0.7, alpha=0.4)

# Highlight where the exponential approx fails
ax1.axvspan(-0.15, 4 * VT, color="gray", alpha=0.08)
ax1.text(
    -0.07,
    1e-9,
    "exp. approx.\nfails ($-1$ matters)",
    fontsize=8,
    color="gray",
    style="italic",
    ha="center",
    va="center",
)

ax1.set_xlim(-0.15, 0.85)
ax1.set_ylim(1e-14, 5e-2)
ax1.set_xlabel(r"$V_D$ (V)")
ax1.set_ylabel(r"$|I_D|$ (A)")
ax1.set_title(
    r"(a) Si PN signal diode $I$-$V$ (1N4148: $n=1.85$, $T=300$ K)", fontsize=10, pad=8
)
ax1.grid(True, which="major", alpha=0.3)
ax1.grid(True, which="minor", alpha=0.1)
ax1.legend(loc="lower right", fontsize=9, framealpha=0.9)

# ---------- Panel (b): regime ruler on log v_hat_d ----------
ax2.set_xscale("log")
ax2.set_xlim(1e-4, 2.0)
ax2.set_ylim(0, 1)
ax2.set_yticks([])

# Coloured bands
y_lo, y_hi = 0.25, 0.65
ax2.axvspan(1e-4, v_lin, ymin=y_lo, ymax=y_hi, color="#27ae60", alpha=0.45)
ax2.axvspan(v_lin, v_quad, ymin=y_lo, ymax=y_hi, color="#2980b9", alpha=0.40)
ax2.axvspan(v_quad, v_interm, ymin=y_lo, ymax=y_hi, color="#e67e22", alpha=0.40)
ax2.axvspan(v_interm, 2.0, ymin=y_lo, ymax=y_hi, color="#c0392b", alpha=0.40)

# Region labels above
ax2.text(np.sqrt(1e-4 * v_lin), 0.82, "Linear", ha="center", va="center", fontsize=8.5)
ax2.text(
    np.sqrt(v_lin * v_quad),
    0.82,
    "Quadratic /\nsquare-law",
    ha="center",
    va="center",
    fontsize=8.5,
)
ax2.text(
    np.sqrt(v_quad * v_interm),
    0.82,
    "Intermediate\nexponential",
    ha="center",
    va="center",
    fontsize=8.5,
)
ax2.text(
    np.sqrt(v_interm * 2.0),
    0.82,
    "Large-signal /\nrectifying",
    ha="center",
    va="center",
    fontsize=8.5,
)

# Boundary labels below
for v, label in [
    (v_lin, r"$0.04\,nV_T$" + "\n" + r"$\sim 1.9$ mV"),
    (v_quad, r"$nV_T$" + "\n" + r"$\sim 48$ mV"),
    (v_interm, r"$V_Q-4V_T$" + "\n" + r"$\sim 446$ mV"),
]:
    ax2.plot([v, v], [y_lo, y_hi], color="black", linewidth=0.6)
    ax2.text(v, 0.12, label, ha="center", va="center", fontsize=8)

ax2.set_xlabel(r"AC amplitude $\hat{v}_d$ (V, log scale)")
ax2.set_title("(b) Operating regimes vs. AC drive amplitude", fontsize=10, pad=8)
ax2.grid(True, axis="x", which="major", alpha=0.25)
ax2.tick_params(axis="x", which="minor", length=2)

# Remove top/right spines for cleaner look on panel b
for spine in ["top", "right", "left"]:
    ax2.spines[spine].set_visible(False)

# Export as vector graphic (PDF ignores DPI, making it redundant)
plt.savefig("regimes_figure.pdf", format="pdf", bbox_inches="tight")
