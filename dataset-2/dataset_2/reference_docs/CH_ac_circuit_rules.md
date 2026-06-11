# CH ac circuit rules

CH series RLC impedance. Z = sqrt(R^2 + (X_L - X_C)^2). Current is I = U/Z. Use RMS quantities unless the problem states peak values.

CH inductive reactance. X_L = omega*L = 2*pi*f*L. Convert mH to H and kHz to Hz.

CH capacitive reactance. X_C = 1/(omega*C) = 1/(2*pi*f*C). Convert microF, nF, pF to F.

CH phase behavior. If X_L > X_C the circuit is inductive and current lags voltage. If X_C > X_L the circuit is capacitive and current leads voltage.

CH power factor. cos(phi) = R/Z for series RLC. Active power P = U*I*cos(phi) = I^2*R.

CH voltage across components. U_R = I*R, U_L = I*X_L, U_C = I*X_C. In AC, U is not generally the arithmetic sum of component voltages.

CH vector voltage relation. For series RLC, U^2 = U_R^2 + (U_L - U_C)^2. Use phasor subtraction for reactive voltages.

CH resonance condition. X_L = X_C, omega0 = 1/sqrt(L*C), f0 = 1/(2*pi*sqrt(L*C)).

CH at resonance. Z = R, I is maximum, cos(phi)=1, U_L and U_C can be large and opposite in phase.

CH quality factor. Q_factor = omega0*L/R = 1/(omega0*C*R). Higher Q means sharper resonance and larger reactive voltage magnification.

CH apparent power. S = U*I in VA. Reactive power Q_r = U*I*sin(phi) in VAR. Active power P is in W.

CH if frequency increases, X_L increases linearly and X_C decreases inversely. Use this to determine inductive or capacitive behavior qualitatively.

CH if the problem gives peak voltage U0, RMS voltage is U0/sqrt(2). If it gives RMS, do not convert again.

CH if asked for heat on resistor over time, use energy A = P*t = I^2*R*t for RMS current.

CH if asked for current amplitude, compute RMS current then multiply by sqrt(2), unless voltage was already amplitude.

CH parallel AC circuits require admittance methods, not the series impedance formula. Use only if the problem states series.

CH unit traps. Resistance in kOhm, inductance in mH, capacitance in microF, frequency in kHz must all be converted before formula use.

CH angular frequency omega is in rad/s. Frequency f is in Hz. Do not substitute f where omega is required.

CH if R changes at resonance, f0 does not change for ideal series RLC, but current and Q factor change.

CH if L or C changes, f0 changes with inverse square root of LC.

CH if asked whether current leads or lags, compare X_L and X_C, not L and C directly.

CH if asked for impedance minimum, it occurs at resonance and equals R for series RLC.

CH if asked for maximum power transfer in this context, maximum AC power in series RLC occurs at resonance for fixed U and R.

CH if U_L equals U_C, this is resonance even if each reactive voltage is not zero.

CH answer_type is quantitative for numeric impedance/current/power and qualitative for lead-lag or increase-decrease questions.

CH final sanity check: Z is always at least R in a series RLC circuit.
