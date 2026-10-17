# -*- coding: utf-8 -*-
"""
Power-law fit for energy-decline curves.

Fits E(t) = a * t^{-b} + c (power law) and E(t) = a * exp(-b t) + c
(exponential), returning the model with higher R2.

Mirrors the original paper's energy-decline fitting.
"""

import numpy as np
from scipy.optimize import curve_fit
from typing import List, Dict, Optional


def power_law(x, a, b, c):
    return a * np.power(x, -b) + c


def exp_decay(x, a, b, c):
    return a * np.exp(-b * x) + c


def fit_energy_curve(energy_history: List[float]) -> Optional[Dict]:
    if len(energy_history) < 10:
        return None

    x = np.arange(len(energy_history), dtype=float)
    y = np.array(energy_history, dtype=float)

    candidates = {}

    # Power law
    try:
        popt, _ = curve_fit(
            power_law, x, y,
            p0=[y[0] - y[-1], 0.5, y[-1]],
            maxfev=5000,
        )
        residuals = y - power_law(x, *popt)
        ss_res = float(np.sum(residuals ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        candidates["power"] = {
            "a": float(popt[0]),
            "b": float(popt[1]),
            "c": float(popt[2]),
            "r2": float(r2),
            "rmse": float(np.sqrt(np.mean(residuals ** 2))),
        }
    except Exception:
        pass

    # Exponential
    try:
        popt, _ = curve_fit(
            exp_decay, x, y,
            p0=[y[0] - y[-1], 0.001, y[-1]],
            maxfev=5000,
        )
        residuals = y - exp_decay(x, *popt)
        ss_res = float(np.sum(residuals ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        candidates["exp"] = {
            "a": float(popt[0]),
            "b": float(popt[1]),
            "c": float(popt[2]),
            "r2": float(r2),
            "rmse": float(np.sqrt(np.mean(residuals ** 2))),
        }
    except Exception:
        pass

    if not candidates:
        return None

    best_name = max(candidates, key=lambda k: candidates[k]["r2"])
    return {"model": best_name, **candidates[best_name]}