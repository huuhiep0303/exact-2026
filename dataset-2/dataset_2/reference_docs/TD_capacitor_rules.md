# TD capacitor rules

TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing.

TD charge-voltage relation. Q = C*U. If C is in microfarads convert to farads. If Q is requested in microC or nC, convert final SI charge back to requested unit.

TD energy formulas. W = 0.5*C*U^2 = Q^2/(2*C) = 0.5*Q*U. Choose the form matching the known constants.

TD disconnected capacitor. Once disconnected from the source, Q remains constant. If C changes, U = Q/C and W = Q^2/(2C).

TD connected capacitor. While connected to the voltage source, U remains constant. If C changes, Q = C*U and W = 0.5*C*U^2 change with C.

TD dielectric inserted disconnected. C increases by epsilon_r, Q constant, U decreases by epsilon_r, and energy decreases by epsilon_r.

TD dielectric inserted connected. U constant, C increases by epsilon_r, Q increases by epsilon_r, and energy increases by epsilon_r.

TD plate distance doubled. Since C is inversely proportional to d, C_new = C/2. Connected and disconnected cases then differ by which quantity stays fixed.

TD plate area doubled. Since C is proportional to A, C_new = 2*C. Connected and disconnected cases then differ by U or Q.

TD series capacitors. 1/Ceq = 1/C1 + 1/C2 + ... . Charge is the same on each capacitor and voltages add.

TD parallel capacitors. Ceq = C1 + C2 + ... . Voltage is the same on each capacitor and charges add.

TD two capacitors in series with voltage U. Compute Ceq first, then Q = Ceq*U, then U_i = Q/C_i.

TD two capacitors in parallel with voltage U. Compute each charge Q_i = C_i*U, then Q_total = sum(Q_i).

TD merging like-sign plates. Total charge is Q1 + Q2 and total capacitance is C1 + C2. Final voltage is U = (Q1+Q2)/(C1+C2).

TD merging unlike-sign plates. Effective total charge is abs(Q1-Q2). Final voltage is abs(Q1-Q2)/(C1+C2).

TD electric field between plates. E = U/d. If U changes because the capacitor is disconnected, update U before computing E.

TD energy density between plates. Energy density w = 0.5*epsilon0*epsilon_r*E^2. Total energy W = w*A*d.

TD spherical or cylindrical capacitor questions should not use parallel plate formula unless the problem explicitly approximates as parallel plates.

TD output unit traps. Capacitance may be requested in microF, nF, or pF. Compute in F first and divide by the prefix factor at the end.

TD if the question says battery is removed, isolated, or disconnected, treat it as Q constant even if voltage was initially given.

TD if the question says still connected, connected to source, or voltage maintained, treat it as U constant.

TD if both dielectric and distance change, combine factors multiplicatively: C_new/C_old = epsilon_r*(A_new/A_old)*(d_old/d_new).

TD if charge is conserved during reconnection of isolated capacitors, total charge before equals total charge after, with sign determined by connected plates.

TD if asked for percentage change, compute (new-old)/old*100 percent after deriving the ratio.

TD qualitative capacitor answers should state whether C, Q, U, W increase, decrease, or stay constant based on source state.

TD final sanity check: increasing capacitance at fixed voltage increases stored energy; increasing capacitance at fixed charge decreases stored energy.
