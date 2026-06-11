# LD coulomb force field

LD Coulomb direct force. Convert every charge to coulomb and every distance to metre before using F = k*abs(q1*q2)/r^2. In air use k = 9e9 unless the problem gives another value. The output unit for force is newton N.

LD force direction. Same sign charges repel and opposite sign charges attract. For force on a test charge, decide the direction of each source force before adding magnitudes. A wrong sign usually gives add instead of subtract.

LD collinear three-charge case. If A, C, B are on one line, compare the directions of F13 and F23 on q3. Same direction gives F_net = F13 + F23. Opposite directions gives F_net = abs(F13 - F23).

LD midpoint symmetry. At the midpoint between two equal same-sign charges, electric fields cancel. At the midpoint between equal opposite-sign charges, electric fields add in the same direction from positive toward negative.

LD electric field magnitude. Use E = k*abs(q)/r^2 for each point charge. Electric field direction is away from positive charge and toward negative charge. Net E is a vector sum, not scalar sum.

LD force from electric field. After computing net field at a point, use F = q0*E for a charge placed there. If q0 is negative, the force direction is opposite the electric field direction.

LD right triangle geometry. If the force vectors are perpendicular, use F_net = sqrt(F1^2 + F2^2). If a missing side is needed, use Pythagoras after converting cm or mm to m.

LD equilateral triangle geometry. All sides are equal and internal angles are 60 degrees. Two equal force vectors at one vertex combine to F*sqrt(3), not 2F.

LD square geometry. A square side a has diagonal a*sqrt(2). The center is at distance a*sqrt(2)/2 from every vertex. Identical charges at symmetric vertices can cancel at the center.

LD perpendicular bisector. A point on the perpendicular bisector of AB is equidistant from A and B. Use r = sqrt((AB/2)^2 + h^2). Decompose vector components along AB and along the bisector.

LD zero electric field same sign. For two same-sign charges, the E=0 point lies between them. Solve k*abs(q1)/r1^2 = k*abs(q2)/r2^2 with r1 + r2 = d.

LD zero electric field opposite sign. For two opposite-sign charges, the E=0 point lies outside the segment, on the side of the smaller absolute charge. Do not place it between the charges.

LD point-charge ratio. From equal field magnitudes, abs(q1)/r1^2 = abs(q2)/r2^2, so r1/r2 = sqrt(abs(q1)/abs(q2)). Use this ratio with the geometry constraint.

LD vector angle formula. For two vectors forming angle theta, use sqrt(F1^2 + F2^2 + 2*F1*F2*cos(theta)). Convert theta to radians before using Python math.cos.

LD cancellation by symmetry. If identical charges are arranged symmetrically around a point, equal magnitude vectors can cancel. Verify directions before declaring zero.

LD nonzero at center with unequal charges. Symmetry only cancels identical symmetric charges. If one charge differs in magnitude or sign, compute components explicitly.

LD unit pitfalls. nC means 1e-9 C, microC means 1e-6 C, cm means 1e-2 m. Squared distance uses the converted metre value squared.

LD common output. Force answers should normally be numeric in N. Field answers should normally be numeric in V/m or N/C. Location questions may be symbolic or distance in m/cm as requested.

LD if the question asks magnitude only, return positive magnitude. If the question asks direction, include direction text or sign convention in explanation.

LD if charges are given as q and -q, preserve signs for direction and field, but Coulomb magnitude uses abs(q1*q2).

LD if a point is closer to one charge, that charge often dominates because field and force scale as 1/r^2. Use this as a sanity check.

LD for a third charge problem, never retrieve only E=0 or V=0 formulas unless the wording explicitly asks for a zero point.

LD for field at a triangle vertex, draw vectors along the two sides meeting the vertex. The angle between vectors is the geometric angle at that vertex.

LD for an equilateral center problem, directions from the center to vertices are separated by 120 degrees, not 60 degrees.

LD for charges on a line, choose a positive axis and assign signed components before summing. This avoids attraction/repulsion mistakes.

LD final sanity check: larger charge or shorter distance increases force/field; doubling distance divides magnitude by four.
