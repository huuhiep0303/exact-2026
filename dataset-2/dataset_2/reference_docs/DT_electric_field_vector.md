# DT electric field vector rules

DT electric field from one point charge. Use E = k*abs(q)/r^2 for the magnitude. In air use k = 9e9 unless the problem gives another constant. Convert all charges to coulomb and all distances to metre before squaring distance.

DT electric field is a vector. Compute each source field magnitude, determine its direction, resolve into signed components, then sum components. Do not add scalar magnitudes unless the directions are proven to be the same.

DT field direction. A positive source charge creates an electric field pointing away from the charge. A negative source charge creates an electric field pointing toward the charge.

DT electric field units. N/C and V/m are equivalent units for electric field strength.

DT collinear field geometry. When points are on one line, choose a positive axis and assign each electric field a signed direction before summing. If two fields point in the same direction, magnitudes add. If they point in opposite directions, subtract magnitudes.

DT collinear geometry detection. If two smaller named distances add to the larger named distance, the three points are collinear and the shared point lies between the two endpoints. For example, if AM + MB = AB, then M lies between A and B.

DT midpoint symmetry. At the midpoint between two equal same-sign charges, electric fields have equal magnitude and opposite directions, so E_net = 0. At the midpoint between two equal opposite-sign charges, the fields point in the same direction from positive toward negative and magnitudes add.

DT perpendicular bisector geometry. A point on the perpendicular bisector of AB is equidistant from charges at A and B. Use r = sqrt((AB/2)^2 + h^2), then decompose each field into a component along AB and a component along the perpendicular bisector.

DT perpendicular bisector equal same-sign charges. For q1 = q2 = q with AB = 2a and point M at distance h from AB on the perpendicular bisector, the components along AB cancel and the components along the bisector add: E = 2*k*abs(q)*h/(a^2 + h^2)^(3/2).

DT perpendicular bisector maximum. For two equal same-sign charges separated by AB = 2a, the field magnitude on the perpendicular bisector E(h) = 2*k*abs(q)*h/(a^2 + h^2)^(3/2) is maximum at h = a/sqrt(2).

DT force on a test charge from electric field. If the question asks for the force on q3 at a point, compute the net electric field E_net at that point first. The force magnitude is F = abs(q3)*abs(E_net). If direction is not requested, return a positive magnitude in N.

DT force direction for a test charge. A positive test charge experiences force in the direction of E_net. A negative test charge experiences force opposite to E_net. The force magnitude remains abs(q3)*abs(E_net).

DT zero electric field same-sign charges. For two source charges with the same sign, the E = 0 point lies between the charges. Solve k*abs(q1)/r1^2 = k*abs(q2)/r2^2 with r1 + r2 = d.

DT zero electric field opposite-sign charges. For two source charges with opposite signs, the E = 0 point lies outside the segment between the charges, on the side of the charge with smaller absolute magnitude. Do not place the zero-field point between opposite-sign charges.

DT zero field distance ratio. From k*abs(q1)/r1^2 = k*abs(q2)/r2^2, use r1/r2 = sqrt(abs(q1)/abs(q2)). Combine this ratio with the correct geometry constraint for the valid region.

DT E=0 versus V=0. Electric field is vector and potential is scalar. If the question asks where the electric field is zero, do not use V = 0 or zero-potential formulas.

DT right triangle vector field. If the two field vectors are perpendicular, use E_net = sqrt(E1^2 + E2^2). If the angle theta between vectors is known, use E_net = sqrt(E1^2 + E2^2 + 2*E1*E2*cos(theta)).

DT field at a triangle vertex. Draw each field vector along the line from the source charge to the target point. Use the geometric angle at the target point for vector addition, and account for sign by direction.

DT square center field. For charges at vertices of a square, the distance from each vertex to the center is a*sqrt(2)/2. Identical charges at opposite symmetric vertices can cancel; mixed signs or unequal magnitudes require component summation.

DT final sanity checks. Shorter distance or larger absolute charge gives a larger field contribution because E scales as abs(q)/r^2. A zero result requires proven symmetry or a solved cancellation point, not just equal distances.
