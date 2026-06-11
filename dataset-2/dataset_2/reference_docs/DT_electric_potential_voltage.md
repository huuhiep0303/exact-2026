# DT electric potential voltage

DT electric potential is scalar. Use V = k*q/r and keep the algebraic sign of q. Do not use vector components for potential.

DT potential superposition. V_total = V1 + V2 + ... with signs. Positive charge contributes positive potential, negative charge contributes negative potential.

DT zero potential with opposite charges. Solve k*q1/r1 + k*q2/r2 = 0. The result is a distance ratio, not a vector cancellation.

DT zero potential with equal opposite charges. The midpoint has V = 0, and every point on the perpendicular bisector has V = 0 if distances are equal.

DT electric field is different from potential. E is vector and V is scalar. A point can have V=0 while E is not zero.

DT potential difference. U_AB = V_A - V_B. Work by electric force on charge q is W = q*(V_A - V_B).

DT sign of work. If q is positive, positive W means motion from higher potential to lower potential. If q is negative, the sign reverses.

DT uniform field. Between parallel plates, E = U/d. Convert d to m. Potential decreases in the direction of the electric field.

DT relation E and V. In a uniform field, U = E*d along the field direction. For point charges, E magnitude scales as 1/r^2 but V scales as 1/r.

DT symbolic answers. If the problem gives variables a, q, k instead of numbers, return an expression using those variables. Do not invent numerical values.

DT equilateral geometry for potential. At a vertex or center, use equal distances when the geometry says equilateral. Since V is scalar, equal opposite charges can cancel algebraically.

DT perpendicular bisector. Points on the perpendicular bisector are equidistant from the two charges. For equal opposite charges, potential contributions cancel.

DT midpoint formula. At midpoint of AB, r1 = r2 = AB/2. V = k*(q1 + q2)/(AB/2).

DT voltage unit. Potential and potential difference use volt V. Work uses joule J after multiplying by charge in C.

DT common trap. Do not use Pythagoras to combine potentials. Pythagoras is for perpendicular vector fields or forces, not scalar potential.

DT if potential asks for maximum or minimum along a line, inspect distance and charge signs. Potential magnitude increases as r becomes smaller.

DT for two same-sign charges, V=0 generally has no finite point if both charges are positive. Same negative charges also do not cancel to zero with positive distances.

DT for opposite unequal charges, zero-potential points can occur between and outside depending on wording and allowed domain. Solve algebraically.

DT if the question asks electric field from potential gradient, use E = -dV/dr and state direction from high V to low V.

DT if q is moved between points, use delta potential energy Delta_U = q*(V_B - V_A), while work by field is q*(V_A - V_B).

DT check dimensions: k*q/r gives volt because N*m^2/C^2 times C divided by m equals N*m/C = J/C.

DT for point charge potential ratio, V_A/V_B = r_B/r_A for the same source charge.

DT for field ratio, E_A/E_B = (r_B/r_A)^2. Do not confuse this with potential ratio.

DT when a plate capacitor appears in a voltage question, decide whether it is uniform-field U=E*d or capacitance Q=C*U.

DT answer_type often symbolic for zero-location and algebraic variable questions; numeric for direct V, U, E, W calculations.

DT final sanity check: potential can be negative. Do not normalize away the sign unless the question asks magnitude only.
