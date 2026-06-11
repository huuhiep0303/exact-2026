"""
Topic-specific solver instructions.

These are selected from the question text by app.modules.topic_router. They are
not tied to dataset IDs, so they work for user-entered questions too.
"""


TOPIC_PROMPTS: dict[str, str] = {
    "coulomb_force": """Topic: Coulomb force / electric force vector problems.
- Use this mode when the question asks for force on a charge, especially q3/test charge.
- Use Coulomb constant k = 9e9 N*m^2/C^2 unless the question states another value.
- Identify every given charge and every given distance. Convert cm to m and micro/nano/milli Coulomb to C.
- For a third charge problem, compute each component force separately:
  F13 = k*abs(q1*q3)/r13**2 and F23 = k*abs(q2*q3)/r23**2.
- Determine force direction from signs: same-sign charges repel, opposite-sign charges attract.
- For collinear A-C-B geometry, decide direction before adding:
  same direction => F_net = F13 + F23; opposite direction => F_net = abs(F13 - F23).
- Use the given distances to infer geometry. If CA + CB = AB, then C lies between A and B.
- If geometry facts are provided, treat them as hard constraints.
- Do not use collinear formulas unless geometry facts or distances prove collinearity.
- For right triangles, use the correct hypotenuse: the side opposite the right angle is the hypotenuse.
- For perpendicular bisector geometry, compute source-to-test distance with r = sqrt((AB/2)^2 + h^2). The horizontal components add: F_net = 2 * F13 * cos(theta), where cos(theta) = h/r or (AB/2)/r depending on direction.
- Output angles in degrees, not radians.
- Combine forces as vectors, not as plain scalars. Use law of cosines when an angle is known.
- Never use a 'point where E = 0' or 'point where V = 0' premise unless the question explicitly asks for that point.
- Do not assume midpoint, equal distances, or an angle unless stated or derived from the geometry.""",

    "electric_field_zero": """Topic: zero electric field location.
- Use this mode only when the question asks where the net electric field is zero.
- Set magnitudes equal only because the two field vectors must cancel at the zero-field point.
- For same-sign charges, the zero-field point lies between the charges.
- For opposite-sign charges, the zero-field point lies outside the segment on the side of the smaller charge (closer to the charge with smaller absolute magnitude).
- Set up the equation k * |q1| / r1**2 = k * |q2| / r2**2. Taking the square root of both sides gives: sqrt(|q1|)/r1 = sqrt(|q2|)/r2.
- Solve for the requested distance/location; do not calculate force on q3 unless q3 is explicitly requested.""",

    "electric_potential": """Topic: electric potential / voltage.
- Use electric potential formulas such as V = k*q/r and superposition V_total = sum(V_i).
- Potential is scalar; add signed values with their signs algebraically, not as vectors.
- Use V = 0 premises only when the question asks for a zero-potential point.
- Do not use force or zero-field formulas unless the question explicitly asks for force or electric field.""",

    "capacitor": """Topic: capacitors.
- Identify C, U/V, Q, d, area, dielectric constant, and source connection state.
- Convert pF, nF, microfarad to F; mC, microcoulomb, nC to C.
- Use Q = C*U, W = 0.5*C*U**2 = Q**2/(2*C) = Q*U/2, and C = epsilon0*epsilon*A/d as appropriate.
- IF DISCONNECTED from source: the charge Q remains constant (Q = C_initial * U_initial). Moving plates or inserting dielectric changes C and U, but NOT Q.
- IF REMAIN CONNECTED to source: the voltage U remains constant (U = U_initial). Moving plates or inserting dielectric changes C and Q, but NOT U.
- Do not invent numerical dielectric constants or symbolic placeholder values.""",

    "dc_circuit": """Topic: practical DC circuits, lamps, and resistor branches.
- Use this mode for lamp/branch/resistor networks with DC voltage, current, resistance, or power.
- For parallel branches: each branch has the same voltage U, branch current is I_i = U / R_i, and total current is I_total = sum(I_i).
- Equivalent resistance in parallel: 1/R_eq = 1/R1 + 1/R2 + ... . For two branches, R_eq = R1*R2/(R1+R2).
- For series resistors: R_eq = R1 + R2 + ... and current is the same through all components.
- Power is P = U*I = I**2*R = U**2/R. Total power is the sum of branch powers or P_total = U*I_total.
- If a parallel branch is removed, recompute total current using the remaining branches only.
- If a branch resistance decreases at fixed voltage, that branch current increases and the lamp usually shines brighter.
- Return multi-value answers as a descriptive string when the question asks for several currents.""",

    "ac_circuit": """Topic: AC/RLC circuit.
- Convert frequency, capacitance, inductance, resistance to SI units.
- Use X_L = 2*pi*f*L, X_C = 1/(2*pi*f*C), Z = sqrt(R**2 + (X_L-X_C)**2).
- Resonance occurs when X_L = X_C or f0 = 1/(2*pi*sqrt(L*C)).
- For yes/no resonance questions, compare the operating frequency to f0.
- If the question asks a Yes/No question (e.g., resonance occurs?), you must output exactly "Yes" or "No" as the final answer (without any extra characters or punctuation like dashes).""",

    "magnetism_induction": """Topic: magnetism, solenoids, inductors, induction.
- Use B = mu0*n*I = mu0*(N/l)*I for long solenoids.
- Use L = mu0*N**2*A/l for solenoid inductance when applicable.
- Use W = 0.5*L*I**2 for magnetic field energy in an inductor.
- Magnetic flux is Phi = N * B * A * cos(theta). Maximum magnetic flux is N * B * A.
- When calculating EMF (electromotive force), compute the magnitude (absolute value) as abs(dPhi/dt) unless direction/sign is explicitly requested.
- Convert cm^2 to m^2 and mH to H before calculation.""",

    "measurement_error": """Topic: measurement error and uncertainty.
- Use deterministic error propagation rules, not physics force/field formulas.
- Instrument absolute error is the FULL least count (LCNS) of the instrument, NOT half the least count. Do NOT divide by 2.
- Relative error = absolute_error / measured_value; percent error = relative_error*100.
- For products/quotients, relative errors add: Z = X * Y or X / Y => delta_Z/Z = delta_X/X + delta_Y/Y.
- For sums/differences, absolute errors add: Z = X + Y or X - Y => delta_Z = delta_X + delta_Y.
- Percent error should be formatted as a number, e.g. 5 or 1.2, not 0.05 or 0.012, and the unit should be %.""",

    "energy_oscillation": """Topic: LC oscillations and electromagnetic energy.
- Use capacitor/electric-field energy W_C = 0.5*C*U**2 and inductor/magnetic-field energy W_L = 0.5*L*I**2.
- In ideal LC oscillations, total energy is conserved.
- To solve inverse questions: U = sqrt(2*W/C), I = sqrt(2*W/L), C = 2*W/U**2, L = 2*W/I**2.
- Compute in SI units first, then convert the final answer back to the requested output unit such as mJ, μF, H, or A.
- Use omega = 1/sqrt(L*C), T = 2*pi*sqrt(L*C), and f = 1/T when asked.""",

    "general": """Topic: general physics problem.
- Select only formulas that directly match the requested quantity.
- Prefer the retrieved premises, but ignore any premise whose use-case does not match the question.
- Do not invent numerical values. If the question lacks enough data for a numeric result, return a descriptive answer.""",
}


def get_topic_prompt(topic: str) -> str:
    """Return topic-specific instructions, falling back to the general prompt."""
    return TOPIC_PROMPTS.get(topic, TOPIC_PROMPTS["general"])
