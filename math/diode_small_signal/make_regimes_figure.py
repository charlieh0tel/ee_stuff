#!/usr/bin/env python3

"""
Generate regime-boundary figure for diode small-signal note.
Fully configured for native LaTeX integration.
"""

import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass

# Physical constants (CODATA 2019)
K_OVER_Q = 8.617333262e-5  # Boltzmann/elementary charge, V/K


@dataclass
class Diode:
    name: str
    description: str
    n: float
    VQ: float
    IS: float
    T: int

    @property
    def VT(self):
        return K_OVER_Q * self.T

    @property
    def IQ(self):
        return self.IS * np.exp(self.VQ / (self.n * self.VT))

    @property
    def v_lin(self):
        return 0.04 * self.n * self.VT

    @property
    def v_quad(self):
        return self.n * self.VT

    @property
    def v_interm(self):
        return self.VQ - 4 * self.n * self.VT

    @property
    def v_4nvt(self):
        return 4 * self.n * self.VT


diode = Diode(
    name="1N4148",
    description="Si PN signal diode",
    n=1.85,
    VQ=0.55,
    IS=1.0e-9,
    T=300,
)

V = np.linspace(-0.15, 0.85, 1500)
I = diode.IS * (np.exp(V / (diode.n * diode.VT)) - 1)  # noqa: E741
I_abs = np.maximum(np.abs(I), 1e-15)

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "text.usetex": True,
        "font.size": 10,
        "axes.labelsize": 11,
    }
)

fig = plt.figure(figsize=(6.8, 6.2))
gs = fig.add_gridspec(2, 1, height_ratios=[1.7, 1.0], hspace=0.45)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# ---------- Panel (a): I-V curve ----------
ax1.semilogy(
    V,
    I_abs,
    color="#1f4e79",
    linewidth=1.6,
    label=r"$I_D = I_S(\mathrm{e}^{V_D/nV_T} - 1)$",
)

ax1.plot(diode.VQ, diode.IQ, "o", color="#c0392b", markersize=7, zorder=5)
ax1.annotate(
    rf"Q: $V_Q={diode.VQ}$ V, $I_Q\approx 100\ \mu$A",
    xy=(diode.VQ, diode.IQ),
    xytext=(diode.VQ - 0.35, diode.IQ * 50),
    arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.8),
    fontsize=9,
    color="#c0392b",
    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c0392b", alpha=0.95, lw=0.6),
)

ax1.axvline(diode.v_4nvt, color="gray", linestyle=":", linewidth=0.9)
ax1.text(
    diode.v_4nvt + 0.008,
    1e-13,
    rf"$4nV_T\approx {round(diode.v_4nvt * 1000)}$ mV",
    fontsize=8,
    color="gray",
    ha="left",
    va="bottom",
)
ax1.axvline(diode.VQ, color="#c0392b", linestyle="--", linewidth=0.7, alpha=0.4)

ax1.axvspan(-0.15, diode.v_4nvt, color="gray", alpha=0.08)
ax1.text(
    -0.05,
    2e-8,
    "exp. approx.\nfails ($-1$ matters)",
    fontsize=8,
    color="dimgray",
    style="italic",
    ha="center",
    va="center",
    bbox=dict(
        boxstyle="round,pad=0.25", fc="white", ec="lightgray", alpha=0.95, lw=0.5
    ),
)

ax1.set_xlim(-0.15, 0.85)
ax1.set_ylim(1e-14, 5e-2)
ax1.set_xlabel(r"$V_D$ (V)")
ax1.set_ylabel(r"$|I_D|$ (A)")
ax1.set_title(
    rf"(a) {diode.description} $I$-$V$ ({diode.name}: $n={diode.n}$, $T={diode.T}$ K)",
    fontsize=10,
    pad=8,
)
ax1.grid(True, which="major", alpha=0.3)
ax1.grid(True, which="minor", alpha=0.1)
ax1.legend(loc="lower right", fontsize=9, framealpha=0.9)

# ---------- Panel (b): regime ruler on log v_hat_d ----------
ax2.set_xscale("log")
ax2.set_xlim(1e-4, 2.0)
ax2.set_ylim(0, 1)
ax2.set_yticks([])

y_lo, y_hi = 0.25, 0.65

regions = [
    (1e-4, diode.v_lin, "#27ae60", 0.45, "Linear"),
    (diode.v_lin, diode.v_quad, "#2980b9", 0.40, "Quadratic /\nsquare-law"),
    (diode.v_quad, diode.v_interm, "#e67e22", 0.40, "Intermediate\nexponential"),
    (diode.v_interm, 2.0, "#c0392b", 0.40, "Full-Shockley /\nrectifying"),
]

for v_start, v_end, color, alpha, label in regions:
    ax2.axvspan(v_start, v_end, ymin=y_lo, ymax=y_hi, color=color, alpha=alpha)
    ax2.text(
        np.sqrt(v_start * v_end), 0.82, label, ha="center", va="center", fontsize=8.5
    )

boundaries = [
    (diode.v_lin, r"$0.04\,nV_T$", 1),
    (diode.v_quad, r"$nV_T$", 0),
    (diode.v_interm, r"$V_Q-4nV_T$", 0),
]

for v, formula, decimals in boundaries:
    ax2.plot([v, v], [y_lo, y_hi], color="black", linewidth=0.6)
    v_mv = v * 1000
    val_str = f"{v_mv:.1f}" if decimals > 0 else f"{round(v_mv)}"
    label_text = rf"{formula}" + "\n" + rf"$\sim {val_str}$ mV"
    ax2.text(v, 0.12, label_text, ha="center", va="center", fontsize=8)

ax2.set_xlabel(r"AC amplitude $\hat{v}_d$ (V, log scale)")
ax2.set_title("(b) Operating regimes vs. AC drive amplitude", fontsize=10, pad=8)
ax2.grid(True, axis="x", which="major", alpha=0.25)
ax2.tick_params(axis="x", which="minor", length=2)

for spine in ["top", "right", "left"]:
    ax2.spines[spine].set_visible(False)

plt.savefig("regimes_figure.pdf", format="pdf", bbox_inches="tight")
