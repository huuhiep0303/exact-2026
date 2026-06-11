# NL lc energy oscillation

NL LC energy conservation. In an ideal LC circuit, W_total = W_C + W_L is constant. W_C = 0.5*C*U^2 and W_L = 0.5*L*I^2.

NL maximum energy. At maximum capacitor voltage, all energy is electric: W_total = 0.5*C*U_max^2.

NL maximum current. At maximum inductor current, all energy is magnetic: W_total = 0.5*L*I_max^2.

NL equal energy split. When W_C = W_L, each is W_total/2. Then U = U_max/sqrt(2) and I = I_max/sqrt(2).

NL angular frequency. omega0 = 1/sqrt(L*C). Convert L to H and C to F.

NL period and frequency. T = 2*pi*sqrt(L*C), f = 1/(2*pi*sqrt(L*C)).

NL charge relation. q = C*u. Maximum charge Q_max = C*U_max.

NL current relation. I_max = omega0*Q_max = U_max*sqrt(C/L).

NL time function. q(t)=Q_max*cos(omega*t+phi), i(t)=-omega*Q_max*sin(omega*t+phi), u(t)=q(t)/C.

NL phase relation. Current leads or lags capacitor voltage by pi/2 depending on sign convention. Energy oscillates at twice the charge frequency.

NL if capacitor energy is known at a moment, inductor energy is W_total - W_C.

NL if inductor energy is known at a moment, capacitor energy is W_total - W_L.

NL unit traps. microF to F, mH to H, mJ to J, nJ to J. Convert output back if requested.

NL if U is half Umax, capacitor energy is one quarter total, because energy depends on U squared.

NL if I is half Imax, inductor energy is one quarter total, because energy depends on I squared.

NL if charge is half Qmax, electric energy is one quarter total.

NL if asked number of oscillations in time t, use N = t/T = f*t.

NL if asked time between max electric and max magnetic energy, it is T/4.

NL if resistance is mentioned as nonzero, ideal conservation no longer holds; otherwise assume ideal LC.

NL if the question asks max voltage from energy, Umax = sqrt(2*W/C).

NL if the question asks max current from energy, Imax = sqrt(2*W/L).

NL if the question asks capacitance from period and inductance, C = (T/(2*pi))^2 / L.

NL if the question asks inductance from frequency and capacitance, L = 1/((2*pi*f)^2*C).

NL answer_type is quantitative for energy/frequency/time and qualitative for phase relationship descriptions.

NL common mistake. Do not use W = C*U^2 without the factor 1/2.

NL final sanity check: total energy is never negative and component energies are between 0 and total.
