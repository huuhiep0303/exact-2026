# CHLT ac resonance notes

CHLT Yes No resonance. If the question asks whether the circuit is at resonance, answer exactly Yes or No and use unit dash. Do not return f0 as the final answer.

CHLT resonance check. Compute f0 = 1/(2*pi*sqrt(L*C)) after converting L to H and C to F. Compare given frequency f with f0 using a small tolerance.

CHLT reactance check. Alternatively compute X_L = 2*pi*f*L and X_C = 1/(2*pi*f*C). Resonance occurs when X_L and X_C are equal within tolerance.

CHLT at resonance impedance. For a series RLC circuit, Z_min = R. Current is maximum and equals U/R.

CHLT at resonance power. cos(phi)=1 and P_max = U^2/R = I^2*R.

CHLT quality factor. Q = omega0*L/R = 1/(omega0*C*R). This is dimensionless.

CHLT bandwidth. For series resonance, bandwidth can be approximated as Delta_omega = R/L and Delta_f = R/(2*pi*L) when the course includes bandwidth.

CHLT voltage magnification. At resonance, U_L and U_C may each be Q times source voltage and cancel in phase opposition.

CHLT if f_given is lower than f0, capacitive reactance dominates. If f_given is higher than f0, inductive reactance dominates.

CHLT if the question gives omega instead of f, use omega0 = 1/sqrt(L*C) and compare omega directly.

CHLT if L or C is requested for resonance at given f, rearrange C = 1/((2*pi*f)^2*L) or L = 1/((2*pi*f)^2*C).

CHLT answer format. For Yes No tasks set answer as a string in Python, e.g. answer = "Yes"; unit = "-".

CHLT tolerance. Exact decimal equality is unreliable. Use math.isclose(f_given, f0, rel_tol=0.02) unless the problem gives its own tolerance.

CHLT common mistake. Do not compare L and C directly; compare reactances or resonant frequency.

CHLT common mistake. Do not set answer to True or False because dataset gold format expects Yes or No.

CHLT common mistake. Do not ignore unit conversion for mH, microF, nF, or kHz.

CHLT if source voltage is RMS, current U/R is RMS. Peak current requires multiplying by sqrt(2).

CHLT if resistance changes, f0 is unchanged in ideal RLC, but current maximum and quality factor change.

CHLT if both L and C change by reciprocal factors that keep LC constant, resonant frequency stays constant.

CHLT if asked for condition, answer X_L = X_C or omega L = 1/(omega C).

CHLT if asked for angular resonant frequency, unit is rad/s. If asked for frequency, unit is Hz.

CHLT if asked for period at resonance, T0 = 2*pi*sqrt(L*C).

CHLT if no numeric frequency is given in a Yes No question, compute the missing resonant frequency and explain that a Yes No answer cannot be determined unless compared to operating frequency.

CHLT for multiple-choice style questions, still compute f0 or reactances before choosing.

CHLT answer_type is yes_no for resonance verification, quantitative for f0, Imax, Pmax, Q factor.

CHLT final sanity check: at resonance the reactive term X_L - X_C is zero.
