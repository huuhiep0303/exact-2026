# THCB parallel DC circuit rules

THCB practical DC circuit. Use Ohm law I = U/R for each resistor or lamp branch. Voltage U is in volts, resistance R is in ohms, current I is in amperes.

THCB parallel branches. In a parallel circuit every branch has the same voltage as the source. Compute each branch current separately: I1 = U/R1, I2 = U/R2, then I_total = I1 + I2.

THCB parallel equivalent resistance. 1/R_eq = 1/R1 + 1/R2 + ... . For exactly two parallel resistors, R_eq = R1*R2/(R1+R2).

THCB series circuit. In a series circuit R_eq = R1 + R2 + ... and the same current flows through each resistor.

THCB removed parallel branch. If a lamp or branch is removed from a parallel circuit, recompute total current using only the remaining branches. Do not include the removed branch current.

THCB identical parallel lamps. If identical lamps with resistance R are connected in parallel to voltage U, each lamp current is U/R and total current is number_of_lamps*U/R.

THCB branch current from total. In a parallel circuit with two branches, if I_total and I1 are known, then I2 = I_total - I1.

THCB lamp brightness. Lamp brightness is associated with current and power. At fixed voltage, decreasing resistance increases branch current and power, so the lamp shines brighter.

THCB DC power. P = U*I = I^2*R = U^2/R. Total circuit power is P_total = U*I_total or the sum of branch powers.

THCB multi-value output. If the question asks for currents through each lamp and total current, return a descriptive string containing all requested values with units.

THCB unit sanity. Ohm can be written as Ω or ohm; both mean resistance. Keep current in A unless the question asks for mA.
