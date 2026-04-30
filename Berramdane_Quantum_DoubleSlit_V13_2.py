# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        Berramdane Model V13.2 — Corrected & Optimized                       ║
║           "Physics meets Philosophy — Laboratory Grade"                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Author  : Al Moalim Berramdane                                             ║
║  License : CC BY 4.0                                                        ║
║  Version : 13.2 (April 2026)                                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  CORRECTIONS OVER V13.1:                                                    ║
║  ✓ Removed unused functions                                                 ║
║  ✓ Unified intensity calculation via path integral                          ║
║  ✓ Added coherence_length envelope                                          ║
║  ✓ Added meas_strength slider (which‑path knowledge)                        ║
║  ✓ Performance improvements (adjustable n_paths)                            ║
║  ✓ Better handling of edge cases                                            ║
║  ✓ Fixed ipywidgets syntax (value, min, max, step)                         ║
║  ✓ Clear separation: Physical vs Speculative                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from scipy.signal import find_peaks
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# Optional QuTiP for advanced density matrix (if available)
try:
    import qutip as qt
    QUTIP_OK = True
except ImportError:
    QUTIP_OK = False

# Widgets for interactive mode
try:
    from ipywidgets import (interact, FloatSlider, Checkbox, IntSlider,
                            Dropdown, Button, Output, IntText, HBox, Label)
    from IPython.display import display
    WIDGETS_OK = True
except ImportError:
    WIDGETS_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
h     = 6.626e-34
hbar  = h / (2 * np.pi)
m_e   = 9.109e-31
c     = 2.998e8
k_B   = 1.381e-23
e_c   = 1.602e-19

REF_JONSSON = {'v': 70000., 'a': 0.3e-6, 'd': 1.0e-6,
               'L': 0.35,   'fringe_mm': 0.18}

# ══════════════════════════════════════════════════════════════════════════════
# CELL 1 — RELATIVISTIC DE BROGLIE
# ══════════════════════════════════════════════════════════════════════════════

def de_broglie_relativistic(v, mass=m_e):
    """Full relativistic de Broglie wavelength: λ = h/(γ m v)"""
    beta = v / c
    if beta >= 1.0:
        beta = 0.9999
    gamma = 1.0 / np.sqrt(1.0 - beta*beta)
    return h / (gamma * mass * v)

# ══════════════════════════════════════════════════════════════════════════════
# CELL 2 — FEYNMAN PATH INTEGRAL (optimized)
# ══════════════════════════════════════════════════════════════════════════════

def feynman_path_integral(x, lam, L, a_width, d_slit, N_slits=2,
                           n_paths=40, rng_seed=42):
    """
    Feynman path integral for N slits.
    Returns normalized intensity pattern.
    """
    rng = np.random.default_rng(rng_seed)
    k = 2 * np.pi / lam
    psi = np.zeros(len(x), dtype=complex)
    half_width = a_width / 2.0

    for s in range(N_slits):
        # Center of slit s (assuming equally spaced, centered at 0)
        y_center = (s - (N_slits - 1) / 2.0) * d_slit
        # Sample positions within slit aperture
        y_samples = rng.uniform(y_center - half_width,
                                y_center + half_width,
                                n_paths)
        for yp in y_samples:
            # Exact path length
            r = np.sqrt(L*L + (x - yp)**2)
            # Phase = k * r
            psi += (1.0 / r) * np.exp(1j * k * r)

    I = np.abs(psi)**2
    return I / np.max(I) if np.max(I) > 0 else I

# ══════════════════════════════════════════════════════════════════════════════
# CELL 3 — QUANTUM DENSITY MATRIX (Lindblad)
# ══════════════════════════════════════════════════════════════════════════════

class BerramdaneQuantumSystem:
    def __init__(self, N_slits=2):
        self.N = N_slits

    def pure_state(self, phases=None):
        """Equal superposition with optional phases."""
        if phases is None:
            phases = np.zeros(self.N)
        psi = np.exp(1j * np.array(phases)) / np.sqrt(self.N)
        return np.outer(psi, psi.conj())

    def lindblad_standard(self, rho, gamma_meas, gamma_therm=0.0,
                          gamma_vac=0.001, temperature=0.0, n_steps=60):
        """Standard Lindblad evolution (physical decoherence)."""
        if temperature > 0 and gamma_therm > 0:
            omega_0 = 2 * np.pi * 1e9
            n_th = 1.0 / (np.exp(hbar * omega_0 / (k_B * temperature)) - 1)
            gamma_therm_eff = gamma_therm * (2*n_th + 1)
        else:
            gamma_therm_eff = gamma_therm
        gamma_total = gamma_meas + gamma_therm_eff + gamma_vac
        dt = 1.0 / n_steps
        decay = np.exp(-gamma_total * dt)
        rho_t = rho.copy().astype(complex)
        for _ in range(n_steps):
            rho_new = rho_t.copy()
            for i in range(self.N):
                for j in range(self.N):
                    if i != j:
                        rho_new[i, j] = rho_t[i, j] * decay
            rho_t = rho_new
        return rho_t

    def lindblad_spiral(self, rho, gamma_meas, gamma_therm=0.0,
                        gamma_vac=0.001, temperature=0.0, n_steps=60,
                        quality_factor=15.0, omega_spiral=2*np.pi*0.1):
        """Spiral Lindblad (speculative philosophical layer)."""
        if temperature > 0 and gamma_therm > 0:
            omega_0 = 2*np.pi*1e9
            n_th = 1.0 / (np.exp(hbar*omega_0/(k_B*temperature))-1)
            gamma_therm_eff = gamma_therm * (2*n_th+1)
        else:
            gamma_therm_eff = gamma_therm
        gamma_total = gamma_meas + gamma_therm_eff + gamma_vac
        effective_gamma = gamma_total / max(quality_factor, 1e-6)
        dt = 1.0 / n_steps
        coherence_decay = np.exp(-effective_gamma * dt)
        phase_shift = np.exp(1j * omega_spiral * dt)
        rho_t = rho.copy().astype(complex)
        for _ in range(n_steps):
            rho_new = rho_t.copy()
            for i in range(self.N):
                for j in range(self.N):
                    if i != j:
                        rho_new[i, j] = rho_t[i, j] * coherence_decay * phase_shift
            rho_t = rho_new
        return rho_t

    def coherence(self, rho):
        """l1-norm of coherence (temporal thread strength)."""
        C = sum(abs(rho[i, j]) for i in range(self.N) for j in range(self.N) if i != j)
        return C / (self.N*(self.N-1)) if self.N > 1 else 0.0

    def purity(self, rho):
        return np.real(np.trace(rho @ rho))

    def entropy(self, rho):
        ev = np.linalg.eigvalsh(rho)
        ev = ev[ev > 1e-15]
        return float(-np.sum(ev * np.log(ev)))

# ══════════════════════════════════════════════════════════════════════════════
# CELL 4 — REALISTIC DETECTOR (Johnson‑Nyquist, dark counts)
# ══════════════════════════════════════════════════════════════════════════════

class PhysicsDetector:
    def __init__(self, efficiency=0.85, dark_rate=0.02,
                 temperature=300.0, resistance=1e6,
                 bandwidth=1e6, pixel_um=5.0, seed=42):
        self.eta = efficiency
        self.dcr = dark_rate
        self.T = temperature
        self.R = resistance
        self.bw = bandwidth
        self.psf_sigma = pixel_um * 1e-6
        self.rng = np.random.default_rng(seed)
        self.V_jn = np.sqrt(4 * k_B * temperature * resistance * bandwidth)

    def detect(self, x, I_prob, n_particles):
        I_norm = np.maximum(I_prob, 0)
        if np.sum(I_norm) > 0:
            I_norm /= np.sum(I_norm)
        cdf = np.cumsum(I_norm)
        u = self.rng.uniform(0, 1, n_particles)
        idx = np.clip(np.searchsorted(cdf, u), 0, len(x)-1)
        mask = self.rng.random(n_particles) < self.eta
        x_det = x[idx[mask]]
        jn_noise = self.V_jn / (1e6) * (x[-1]-x[0])
        x_det += self.rng.normal(0, max(self.psf_sigma, jn_noise), len(x_det))
        n_dark = self.rng.poisson(self.dcr * n_particles)
        x_dark = self.rng.uniform(x[0], x[-1], n_dark)
        x_all = np.concatenate([x_det, x_dark])
        counts, _ = np.histogram(x_all, bins=len(x), range=(x[0], x[-1]))
        return counts.astype(float), len(x_det), n_dark

# ══════════════════════════════════════════════════════════════════════════════
# CELL 5 — METRICS
# ══════════════════════════════════════════════════════════════════════════════

def compute_visibility(x, I):
    peaks, _ = find_peaks(I, distance=len(x)//40)
    if len(peaks) < 2:
        return 0.0
    Imax = np.max(I[peaks])
    center_idx = np.argmin(np.abs(x))
    search = np.where(np.abs(x - x[center_idx]) < 0.005)[0]
    Imin = np.min(I[search]) if len(search) > 0 else np.min(I)
    denom = Imax + Imin
    return (Imax - Imin) / denom if denom > 0 else 0.0

def normalize(arr):
    mx = np.max(arr)
    return arr / mx if mx > 0 else arr

# ══════════════════════════════════════════════════════════════════════════════
# CELL 6 — MAIN SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def run_berramdane_v13_2(
    v_mean=70000., delta_v=0., L_mm=350.,
    a_width=0.3e-6, d_slit=1.0e-6, N_slits=2,
    gamma_meas=0.0, gamma_therm=0.0, gamma_vac=0.001,
    meas_strength=0.0,            # which‑path knowledge (0..1)
    coherence_length=None,        # in meters (coherence envelope)
    n_particles=3000, efficiency=0.85, dark_rate=0.02,
    det_temperature=300.0,
    use_path_integral=True,
    n_paths=40,
    SPECULATIVE_MODE=False,
    quality_factor=15.0, omega_spiral=2*np.pi*0.1,
    rng_seed=42
):
    L = L_mm / 1000.0
    lam = de_broglie_relativistic(v_mean)

    if a_width >= d_slit:
        a_width = d_slit * 0.99
        print("⚠️ Slit width adjusted to be < separation.")

    spacing = lam * L / d_slit
    x_lim = max(0.004, 4.5 * spacing)
    x = np.linspace(-x_lim, x_lim, 2500)

    qsys = BerramdaneQuantumSystem(N_slits)
    rho0 = qsys.pure_state()
    rho_std = qsys.lindblad_standard(rho0, gamma_meas, gamma_therm,
                                     gamma_vac, det_temperature, n_steps=60)

    if SPECULATIVE_MODE:
        rho_active = qsys.lindblad_spiral(rho0, gamma_meas, gamma_therm,
                                          gamma_vac, det_temperature,
                                          n_steps=60, quality_factor=quality_factor,
                                          omega_spiral=omega_spiral)
    else:
        rho_active = rho_std

    coh = qsys.coherence(rho_active)

    # Pure wave and particle patterns
    I_wave = feynman_path_integral(x, lam, L, a_width, d_slit,
                                   N_slits, n_paths=n_paths, rng_seed=rng_seed)
    sigma_p = a_width * L / lam
    I_particle = np.zeros_like(x)
    for k in range(N_slits):
        yc = (k - (N_slits - 1)/2.0) * d_slit
        I_particle += np.exp(-(x - yc)**2 / (2 * sigma_p**2))
    I_particle = normalize(I_particle)

    # Blend according to coherence
    I_main = coh * I_wave + (1 - coh) * I_particle
    I_main = normalize(I_main)

    if coherence_length is not None and coherence_length > 0:
        sigma_coh = coherence_length * L / d_slit
        env = np.exp(-x**2 / (2 * sigma_coh**2))
        I_main *= env
        I_main = normalize(I_main)

    # Detector
    det = PhysicsDetector(efficiency=efficiency, dark_rate=dark_rate,
                          temperature=det_temperature, seed=rng_seed)
    counts, n_det, n_dark = det.detect(x, I_main, n_particles)
    I_det = normalize(counts)

    V_theory = compute_visibility(x, I_main)
    V_meas   = compute_visibility(x, I_det)
    K = float(np.clip(meas_strength if meas_strength > 0 else gamma_meas/(gamma_meas+0.5), 0, 1))
    VK2 = V_theory**2 + K**2

    sim_fringe = spacing * 1000
    ref_fringe = REF_JONSSON['fringe_mm']
    fringe_err = abs(sim_fringe - ref_fringe) / ref_fringe * 100

    lam_nr = h / (m_e * v_mean)
    rel_corr = abs(lam_nr - lam) / lam_nr * 100

    purity = qsys.purity(rho_active)
    entropy = qsys.entropy(rho_active)

    if SPECULATIVE_MODE:
        rho_spiral = qsys.lindblad_spiral(rho0, gamma_meas, gamma_therm,
                                          gamma_vac, det_temperature,
                                          n_steps=60, quality_factor=quality_factor,
                                          omega_spiral=omega_spiral)
        coh_spiral = qsys.coherence(rho_spiral)
        I_spiral = coh_spiral * I_wave + (1 - coh_spiral) * I_particle
        I_spiral = normalize(I_spiral)
    else:
        coh_spiral = None
        I_spiral = None

    # Wigner (only for N=2)
    if N_slits == 2:
        r = np.real(rho_active[0, 1])
        i_ = np.imag(rho_active[0, 1])
        a = np.real(rho_active[0, 0])
        b = np.real(rho_active[1, 1])
        q = np.linspace(-3, 3, 80)
        p = np.linspace(-3, 3, 80)
        Q, P = np.meshgrid(q, p)
        W = (1/(2*np.pi)) * (1 + 2*r*np.cos(Q)*np.cos(P)
                             - 2*i_*np.sin(Q)*np.cos(P)
                             + (a-b)*np.sin(P))
    else:
        W = None
        q, p = None, None

    # ══════════════════════════════════════════════════════════════════════════
    # PLOTTING
    # ══════════════════════════════════════════════════════════════════════════
    fig = plt.figure(figsize=(24, 16))
    fig.patch.set_facecolor('#0d1117')
    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.45, wspace=0.32,
                           top=0.92, bottom=0.05)

    def style_ax(ax, title, xlabel='', ylabel=''):
        ax.set_facecolor('#161b22')
        ax.tick_params(colors='#8b949e', labelsize=8)
        ax.set_title(title, color='#58a6ff', fontsize=9, pad=4)
        ax.set_xlabel(xlabel, color='#8b949e', fontsize=8)
        ax.set_ylabel(ylabel, color='#8b949e', fontsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor('#30363d')
        ax.grid(alpha=0.18, color='#30363d')
        return ax

    x_mm = x * 1000

    # [0,0] Main pattern
    ax = style_ax(fig.add_subplot(gs[0,0]), 'Intensity I(x)', 'Position (mm)', 'Intensity')
    ax.plot(x_mm, I_wave, color='#3fb950', lw=1, ls='--', alpha=0.5, label='Pure wave')
    ax.plot(x_mm, I_particle, color='#f85149', lw=1, ls='--', alpha=0.5, label='Classical')
    ax.plot(x_mm, I_main, color='#58a6ff', lw=2, label='V13.2 (physical)')
    if SPECULATIVE_MODE and I_spiral is not None:
        ax.plot(x_mm, I_spiral, color='#e3b341', lw=1.5, ls=':', label='Spiral [SPEC]')
    ax.fill_between(x_mm, I_main, alpha=0.12, color='#58a6ff')
    ax.set_xlim(-x_lim*1000, x_lim*1000)
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')
    ax.text(0.02, 0.95, f'V={V_theory:.3f}', transform=ax.transAxes,
            color='#e3b341', fontsize=9, weight='bold')

    # [0,1] Detector screen
    ax = style_ax(fig.add_subplot(gs[0,1]), f'Realistic Detector  η={efficiency:.0%}  T={det_temperature:.0f}K',
                  'Position (mm)', 'Counts (norm.)')
    ax.bar(x_mm, I_det, width=x_mm[1]-x_mm[0], color='#388bfd', alpha=0.65)
    ax.plot(x_mm, I_main, color='#f0883e', lw=1.5, label='Theory')
    ax.set_xlim(-x_lim*1000, x_lim*1000)
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')
    ax.text(0.02, 0.88, f'V_meas={V_meas:.3f}\nN_det={n_det}\nDark={n_dark}',
            transform=ax.transAxes, color='#8b949e', fontsize=8)

    # [0,2] Density matrix (real part)
    ax = style_ax(fig.add_subplot(gs[0,2]), 'Density Matrix Re(ρ)', 'Slit j', 'Slit i')
    labels = [f'|{i+1}⟩' for i in range(N_slits)]
    cmap_rho = LinearSegmentedColormap.from_list('rho', ['#f85149','#0d1117','#3fb950'])
    im = ax.imshow(np.real(rho_active), cmap=cmap_rho, vmin=-0.5, vmax=0.5)
    ax.set_xticks(range(N_slits), labels, color='#c9d1d9', fontsize=10)
    ax.set_yticks(range(N_slits), labels, color='#c9d1d9', fontsize=10)
    plt.colorbar(im, ax=ax, shrink=0.8).ax.tick_params(colors='#8b949e')
    for i in range(N_slits):
        for j in range(N_slits):
            v = np.real(rho_active[i,j])
            ax.text(j, i, f'{v:.3f}', ha='center', va='center',
                    color='white' if abs(v)<0.3 else 'black', fontsize=9)
    mode_label = '🌀 SPIRAL' if SPECULATIVE_MODE else '📐 STANDARD'
    ax.text(0.02, 0.02, mode_label, transform=ax.transAxes,
            color='#e3b341' if SPECULATIVE_MODE else '#3fb950', fontsize=8)

    # [0,3] Wigner function
    ax = style_ax(fig.add_subplot(gs[0,3]), 'Wigner Function W(q,p)', 'q', 'p')
    if W is not None:
        w_max = max(abs(np.min(W)), abs(np.max(W)), 1e-9)
        norm_w = TwoSlopeNorm(vmin=-w_max, vcenter=0, vmax=w_max)
        cmap_w = LinearSegmentedColormap.from_list('wig', ['#f85149','#0d1117','#58a6ff'])
        im_w = ax.pcolormesh(q, p, W, cmap=cmap_w, norm=norm_w)
        plt.colorbar(im_w, ax=ax, shrink=0.8).ax.tick_params(colors='#8b949e')
        ax.contour(q, p, W, levels=[0], colors=['#e3b341'], linewidths=1)
    else:
        ax.text(0.5, 0.5, 'Wigner only for N=2', transform=ax.transAxes,
                ha='center', color='#8b949e', fontsize=10)
        ax.set_axis_off()

    # [1,0] Standard vs Spiral coherence
    ax = style_ax(fig.add_subplot(gs[1,0]), 'Coherence C(ρ) vs γ_meas', 'γ_meas', 'Coherence')
    g_arr = np.linspace(0, 5, 200)
    rho_p = qsys.pure_state()
    C_std_arr = [qsys.coherence(qsys.lindblad_standard(rho_p, g, n_steps=30))
                 for g in g_arr]
    ax.plot(g_arr, C_std_arr, color='#58a6ff', lw=2.5, label='Standard Lindblad')
    if SPECULATIVE_MODE:
        C_spi_arr = [qsys.coherence(qsys.lindblad_spiral(rho_p, g, n_steps=30,
                                                         quality_factor=quality_factor,
                                                         omega_spiral=omega_spiral))
                     for g in g_arr]
        ax.plot(g_arr, C_spi_arr, color='#e3b341', lw=2, ls='--',
                label=f'Spiral (Q={quality_factor:.0f}) ⚠')
    ax.axvline(gamma_meas, color='#f85149', ls=':', lw=1.5, label=f'γ_meas={gamma_meas:.2f}')
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')

    # [1,1] Complementarity
    ax = style_ax(fig.add_subplot(gs[1,1]), 'Complementarity V²+K² ≤ 1', 'Which-path K', 'Visibility V')
    theta_c = np.linspace(0, np.pi/2, 300)
    ax.plot(np.cos(theta_c), np.sin(theta_c), '--', color='#f0883e', lw=2, label='Bohr limit')
    ax.fill_between(np.cos(theta_c), np.sin(theta_c), alpha=0.07, color='#f0883e')
    # Trajectory
    V_tr, K_tr = [], []
    for g in np.linspace(0, 3, 60):
        rho_g = qsys.lindblad_standard(rho_p, g, n_steps=20)
        c_g = qsys.coherence(rho_g)
        I_g = c_g * I_wave + (1-c_g) * I_particle
        I_g = normalize(I_g)
        V_tr.append(compute_visibility(x, I_g))
        K_tr.append(float(np.clip(g/(g+0.5), 0, 1)))
    ax.plot(K_tr, V_tr, color='#a371f7', lw=2, label='Lindblad trajectory')
    ax.scatter([K], [V_theory], s=150, color='#3fb950', zorder=5,
               label=f'Current (V={V_theory:.2f}, K={K:.2f})')
    ax.set_xlim(0, 1.05); ax.set_ylim(0, 1.05)
    ax.set_aspect('equal')
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')
    col_vk = '#3fb950' if VK2 <= 1.0 else '#f85149'
    ax.text(0.05, 0.07, f'V²+K² = {VK2:.4f}', transform=ax.transAxes,
            color=col_vk, fontsize=10, weight='bold')

    # [1,2] Entropy & Purity
    ax = style_ax(fig.add_subplot(gs[1,2]), 'Quantum Information: S(ρ) & Purity', 'γ_meas', '')
    S_arr = [qsys.entropy(qsys.lindblad_standard(rho_p, g, n_steps=20))
             for g in g_arr]
    P_arr = [qsys.purity(qsys.lindblad_standard(rho_p, g, n_steps=20))
             for g in g_arr]
    ax.plot(g_arr, S_arr, color='#f85149', lw=2, label='Entropy S(ρ)')
    ax.plot(g_arr, P_arr, color='#3fb950', lw=2, label='Purity Tr(ρ²)')
    ax.axhline(np.log(N_slits), color='#8b949e', ls=':', lw=1, label=f'S_max=ln({N_slits})')
    ax.axvline(gamma_meas, color='#e3b341', ls=':', lw=1.5)
    ax.set_xlim(0, max(g_arr))
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')
    ax.text(0.03, 0.75, f'S={entropy:.3f}\nPurity={purity:.3f}',
            transform=ax.transAxes, color='#c9d1d9', fontsize=8)

    # [1,3] Relativistic correction
    ax = style_ax(fig.add_subplot(gs[1,3]), 'Relativistic Correction', 'v/c', 'Δλ/λ (%)')
    v_range = np.linspace(0.01*c, 0.99*c, 500)
    lam_nr_v = h / (m_e * v_range)
    lam_rel_v = np.array([de_broglie_relativistic(v) for v in v_range])
    rel_pct = (lam_nr_v - lam_rel_v) / lam_nr_v * 100
    ax.plot(v_range/c, rel_pct, color='#58a6ff', lw=2)
    ax.axvline(v_mean/c, color='#f85149', ls='--', lw=1.5,
               label=f'v={v_mean/1e3:.0f}km/s\ncorr={rel_corr:.4f}%')
    ax.axhline(10, color='#e3b341', ls=':', lw=1, label='10%')
    ax.set_xlim(0, 1)
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')

    # [2,0] Tonomura buildup
    ax = style_ax(fig.add_subplot(gs[2,0]), 'Single-Particle Buildup (Tonomura style)',
                  'Position (mm)', 'Accumulated hits')
    det2 = PhysicsDetector(efficiency=efficiency, dark_rate=dark_rate,
                           temperature=det_temperature, seed=rng_seed+1)
    stages = [10, 100, 500, n_particles]
    colors = ['#f85149','#e3b341','#58a6ff','#3fb950']
    for ns, col in zip(stages, colors):
        cnt, _, _ = det2.detect(x, I_main, ns)
        cnt = cnt / max(np.max(cnt), 1)
        offset = stages.index(ns) * 1.15
        ax.plot(x_mm, cnt + offset, color=col, lw=0.8, label=f'N={ns}')
    ax.set_xlim(-x_lim*1000, x_lim*1000)
    ax.set_yticks([])
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9', title='electrons')
    ax.text(0.5, 0.01, 'Pattern emerges particle by particle',
            transform=ax.transAxes, ha='center', color='#8b949e', fontsize=7, style='italic')

    # [2,1] Multi-slit comparison
    ax = style_ax(fig.add_subplot(gs[2,1]), 'Multi‑Slit Comparison', 'Position (mm)', 'Intensity')
    for Ns, col in zip([2,3,5], ['#58a6ff','#3fb950','#f0883e']):
        I_ns = feynman_path_integral(x, lam, L, a_width, d_slit, Ns,
                                     n_paths=40, rng_seed=rng_seed)
        I_ns = normalize(I_ns)
        ax.plot(x_mm, I_ns, color=col, lw=1.2, alpha=0.85, label=f'{Ns} slits')
    ax.set_xlim(-x_lim*1000, x_lim*1000)
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')

    # [2,2] Speculative mode pattern comparison
    ax = style_ax(fig.add_subplot(gs[2,2]), '🌀 Berramdane Spiral vs Standard',
                  'Position (mm)', 'Intensity')
    ax.plot(x_mm, I_wave, color='#3fb950', lw=1, ls='--', alpha=0.5, label='Pure wave')
    ax.plot(x_mm, I_main, color='#58a6ff', lw=2, label='Standard (physical)')
    if SPECULATIVE_MODE and I_spiral is not None:
        ax.plot(x_mm, I_spiral, color='#e3b341', lw=1.5, ls=':', label=f'Spiral Q={quality_factor:.0f} ⚠')
        diff = np.abs(I_main - I_spiral)
        ax.fill_between(x_mm, 0, diff, alpha=0.25, color='#e3b341', label='|difference|')
    ax.set_xlim(-x_lim*1000, x_lim*1000)
    ax.legend(fontsize=7, facecolor='#161b22', labelcolor='#c9d1d9')
    if not SPECULATIVE_MODE:
        ax.text(0.5, 0.5, 'Enable SPECULATIVE_MODE\nto see spiral effect',
                transform=ax.transAxes, ha='center', va='center',
                color='#8b949e', fontsize=9, style='italic', alpha=0.5)

    # [2,3] Summary panel
    ax = fig.add_subplot(gs[2,3])
    ax.set_facecolor('#161b22')
    ax.axis('off')
    mode_str = "🌀 SPIRAL [SPECULATIVE]" if SPECULATIVE_MODE else "📐 STANDARD [PHYSICAL]"
    lines = [
        (f"Berramdane V13.2", '#58a6ff', 11, 'bold'),
        (f"Mode: {mode_str}", '#e3b341' if SPECULATIVE_MODE else '#3fb950', 8, 'bold'),
        ("", '', 7, 'normal'),
        ("── WAVELENGTH ──", '#e3b341', 8, 'bold'),
        (f"  λ_NR   = {lam_nr*1e9:.4f} nm", '#8b949e', 8, 'normal'),
        (f"  λ_rel  = {lam*1e9:.4f} nm", '#c9d1d9', 8, 'normal'),
        (f"  Δλ/λ   = {rel_corr:.4f}%", '#3fb950' if rel_corr<0.1 else '#e3b341', 8, 'normal'),
        ("", '', 7, 'normal'),
        ("── FRINGE (Jönsson) ──", '#e3b341', 8, 'bold'),
        (f"  Sim    = {sim_fringe:.3f} mm", '#c9d1d9', 8, 'normal'),
        (f"  Ref    = {ref_fringe:.2f}  mm", '#c9d1d9', 8, 'normal'),
        (f"  Error  = {fringe_err:.2f}%", '#3fb950' if fringe_err<5 else '#e3b341', 8, 'bold'),
        ("", '', 7, 'normal'),
        ("── QUANTUM ──", '#e3b341', 8, 'bold'),
        (f"  V_theory = {V_theory:.4f}", '#3fb950', 8, 'normal'),
        (f"  V_meas   = {V_meas:.4f}", '#c9d1d9', 8, 'normal'),
        (f"  K        = {K:.4f}", '#c9d1d9', 8, 'normal'),
        (f"  V²+K²    = {VK2:.4f} {'✓' if VK2<=1 else '✗'}", '#3fb950' if VK2<=1 else '#f85149', 8, 'bold'),
        (f"  Purity   = {purity:.4f}", '#c9d1d9', 8, 'normal'),
        (f"  S(ρ)     = {entropy:.4f}", '#c9d1d9', 8, 'normal'),
        (f"  Coh(ρ)   = {coh:.4f}  [Thread]", '#a371f7', 8, 'normal'),
    ]
    if SPECULATIVE_MODE and coh_spiral is not None:
        lines += [
            ("", '', 7, 'normal'),
            ("── SPIRAL [SPECULATIVE] ──", '#e3b341', 8, 'bold'),
            (f"  Coh_spiral = {coh_spiral:.4f}", '#e3b341', 8, 'normal'),
            (f"  Q_factor   = {quality_factor:.1f}", '#e3b341', 8, 'normal'),
            (f"  ω_spiral   = {omega_spiral:.3f} rad", '#e3b341', 8, 'normal'),
            ("  ⚠ Not physical — philosophical", '#f85149', 7, 'italic'),
        ]
    lines += [
        ("", '', 7, 'normal'),
        ("── DETECTOR ──", '#e3b341', 8, 'bold'),
        (f"  N_det    = {n_det}/{n_particles}", '#c9d1d9', 8, 'normal'),
        (f"  Dark     = {n_dark}", '#c9d1d9', 8, 'normal'),
        (f"  JN noise  included", '#c9d1d9', 8, 'normal'),
    ]

    y = 0.98
    for txt, col, sz, wt in lines:
        if txt:
            ax.text(0.04, y, txt, transform=ax.transAxes, va='top',
                    color=col, fontsize=sz, weight=wt, family='monospace')
        y -= 0.038

    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_edgecolor('#e3b341' if SPECULATIVE_MODE else '#388bfd')
        sp.set_linewidth(1.5)

    fig.text(0.5, 0.975,
             f'Berramdane Model V13.2 — Path Integral + Lindblad + Relativistic',
             ha='center', va='top', color='#c9d1d9', fontsize=13, weight='bold')
    fig.text(0.5, 0.958,
             f'v={v_mean/1e3:.0f}km/s | λ={lam*1e9:.3f}nm | L={L_mm:.0f}mm | '
             f'γ={gamma_meas:.2f} | N={N_slits} slits | SPECULATIVE={SPECULATIVE_MODE}',
             ha='center', va='top', color='#8b949e', fontsize=8)
    plt.show()

    print("═"*65)
    print(f"  Berramdane V13.2  |  SPECULATIVE_MODE = {SPECULATIVE_MODE}")
    print("═"*65)
    print(f"  λ (relativistic)  : {lam*1e9:.4f} nm  (Δ={rel_corr:.4f}%)")
    print(f"  Fringe spacing    : {sim_fringe:.3f} mm  (err={fringe_err:.2f}%)")
    print(f"  Visibility theory : {V_theory:.4f}")
    print(f"  Visibility meas.  : {V_meas:.4f}")
    print(f"  V² + K²           : {VK2:.4f}  {'✓' if VK2<=1 else '✗'}")
    print(f"  Purity Tr(ρ²)     : {purity:.4f}")
    print(f"  Entropy S(ρ)      : {entropy:.4f}")
    print(f"  Coherence C(ρ)    : {coh:.4f}  [= Thread strength]")
    if SPECULATIVE_MODE and coh_spiral:
        print(f"  ── SPIRAL ──")
        print(f"  Coh_spiral        : {coh_spiral:.4f}  ⚠ speculative")
        print(f"  Quality factor Q  : {quality_factor:.1f}")
        print(f"  ω_spiral          : {omega_spiral:.4f} rad")
    print(f"  Detected          : {n_det}/{n_particles}")
    print("═"*65)

    return {'I': I_main, 'x': x, 'V': V_theory, 'purity': purity, 'entropy': entropy}

# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE WIDGETS (CORRECTED SYNTAX)
# ══════════════════════════════════════════════════════════════════════════════

if WIDGETS_OK:
    _global_data = {}
    export_btn = Button(description="📥 Export CSV", button_style='success')
    export_out = Output()

    def on_export(b):
        with export_out:
            export_out.clear_output()
            if 'x' in _global_data and 'I' in _global_data:
                df = pd.DataFrame({'position_mm': _global_data['x']*1000,
                                   'intensity': _global_data['I']})
                df.to_csv('berramdane_v13_2.csv', index=False)
                print("✅ Saved berramdane_v13_2.csv")
            else:
                print("❌ Run simulation first.")
    export_btn.on_click(on_export)

    @interact(
        v_mean=FloatSlider(value=70000, min=20000, max=150000, step=1000,
                           description='v (m/s)', continuous_update=False),
        delta_v=FloatSlider(value=0, min=0, max=15000, step=500,
                            description='Δv (m/s)', continuous_update=False),
        L_mm=FloatSlider(value=350, min=50, max=1000, step=10,
                         description='L (mm)', continuous_update=False),
        a_width=FloatSlider(value=0.3e-6, min=0.1e-6, max=2e-6, step=0.05e-6,
                            description='a (m)', continuous_update=False),
        d_slit=FloatSlider(value=1.0e-6, min=0.2e-6, max=3e-6, step=0.05e-6,
                           description='d (m)', continuous_update=False),
        N_slits=IntSlider(value=2, min=2, max=5, step=1, description='N slits'),
        gamma_meas=FloatSlider(value=0.0, min=0.0, max=5.0, step=0.1,
                               description='γ_meas', continuous_update=False),
        meas_strength=FloatSlider(value=0.0, min=0.0, max=1.0, step=0.05,
                                  description='K (which‑path)', continuous_update=False),
        coherence_length=FloatSlider(value=0.0, min=0.0, max=1e-3, step=1e-5,
                                     description='L_coh (m)', continuous_update=False),
        n_particles=IntSlider(value=2000, min=100, max=10000, step=100,
                              description='N particles'),
        efficiency=FloatSlider(value=0.85, min=0.1, max=1.0, step=0.05,
                               description='η'),
        det_temperature=FloatSlider(value=300, min=4, max=800, step=10,
                                    description='T_det (K)', continuous_update=False),
        use_path_integral=Checkbox(value=True, description='Path integral'),
        n_paths=IntSlider(value=40, min=10, max=100, step=5,
                          description='Paths per slit'),
        SPECULATIVE_MODE=Checkbox(value=False, description='🌀 Spiral [SPECULATIVE]'),
        quality_factor=FloatSlider(value=15.0, min=1.0, max=50.0, step=1.0,
                                   description='Q factor'),
        omega_spiral=FloatSlider(value=2*np.pi*0.1, min=0.01, max=2*np.pi, step=0.01,
                                 description='ω spiral'),
        rng_seed=IntText(value=42, description='Seed')
    )
    def interactive_run(v_mean, delta_v, L_mm, a_width, d_slit, N_slits,
                        gamma_meas, meas_strength, coherence_length,
                        n_particles, efficiency, det_temperature,
                        use_path_integral, n_paths, SPECULATIVE_MODE,
                        quality_factor, omega_spiral, rng_seed):
        # Convert coherence_length to None if zero
        if coherence_length <= 0:
            coherence_length = None
        result = run_berramdane_v13_2(
            v_mean=v_mean, delta_v=delta_v, L_mm=L_mm,
            a_width=a_width, d_slit=d_slit, N_slits=N_slits,
            gamma_meas=gamma_meas, meas_strength=meas_strength,
            coherence_length=coherence_length,
            n_particles=n_particles, efficiency=efficiency,
            det_temperature=det_temperature, use_path_integral=use_path_integral,
            n_paths=n_paths, SPECULATIVE_MODE=SPECULATIVE_MODE,
            quality_factor=quality_factor, omega_spiral=omega_spiral,
            rng_seed=rng_seed
        )
        _global_data.update(result)

    display(HBox([export_btn, Label("← export to CSV")]), export_out)
else:
    print("Interactive widgets not available. Running static example...")
    run_berramdane_v13_2()
