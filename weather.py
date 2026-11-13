from bisect import bisect_right
from datetime import timedelta
from math import exp
from pathlib import Path
from random import Random

import numpy as np
from openpyxl import load_workbook
from scipy.integrate import quad
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq


class WeatherCalendar:
    """Shared continuous-time weather path with right-continuous states."""

    def __init__(self, transitions, initial_wet, end_hour):
        self.transitions = transitions
        self.initial_wet = initial_wet
        self.end_hour = end_hour

    def at(self, hour):
        index = bisect_right(self.transitions, hour)
        wet = self.initial_wet ^ bool(index % 2)
        next_change = (
            self.transitions[index] if index < len(self.transitions) else self.end_hour
        )
        return wet, next_change


def generate_weather(start, end_hour, initial_wet, seed):
    path = Path(__file__).with_name("CTMC_Spline_March_Event_Excluded_01mm.xlsx")
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        knots = np.array(list(book["Spline_Knots"].values)[1:], dtype=float)
    finally:
        book.close()
    if (knots.shape != (12, 3) or not np.all(knots[:, 0] == np.arange(12) + 0.5)
            or not np.isfinite(knots).all() or not (knots[:, 1:] > 0).all()):
        raise ValueError("Spline_Knots must contain 12 month midpoints and positive rates.")
    phases = np.r_[knots[:, 0], 12.5]
    splines = [
        CubicSpline(phases, np.log(np.r_[rates, rates[0]]), bc_type="periodic")
        for rates in knots[:, 1:].T
    ]

    def phase(hour):
        now = start + timedelta(hours=hour)
        month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (month + timedelta(days=32)).replace(day=1)
        return month.month - 1 + (now - month) / (next_month - month)

    rng = Random(seed)
    transitions = []
    wet = initial_wet
    left = 0.0
    while left < end_hour:
        spline = splines[int(wet)]

        def rate(hour):
            return exp(float(spline(phase(hour))))

        target = rng.expovariate(1)
        while left < end_hour:
            right = min(left + 24, end_hour)
            hazard = quad(rate, left, right)[0]
            if hazard >= target:
                change = brentq(
                    lambda hour: quad(rate, left, hour)[0] - target, left, right
                )
                if change < end_hour:
                    transitions.append(change)
                    wet = not wet
                left = change
                break
            target -= hazard
            left = right
    return WeatherCalendar(transitions, initial_wet, end_hour)
