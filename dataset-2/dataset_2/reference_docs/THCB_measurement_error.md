# THCB measurement error

THCB instrument error. In this project use Vietnamese standard Delta_instrument = LCNS (the full least count, NOT LCNS/2). Never divide LCNS by 2.
 
THCB repeated measurements. Compute mean x_bar = sum(x_i)/n before random error.
 
THCB random error. Use Delta_random = max(abs(x_i - x_bar)), not the average deviation.
 
THCB total error. Use Delta_total = max(Delta_random, Delta_instrument) when combining random and instrument error in this dataset.
 
THCB relative error. delta = Delta/abs(X). Percentage error is delta_percent = (Delta/abs(X))*100. Always keep it in percent form (e.g. write 5 or 5% if asked, not 0.05).
 
THCB final measurement format. Write X = x_bar +- Delta_x with unit. If percent is requested, return percentage value with % unit (e.g. 5 % or 2.1 %).

THCB sum and difference propagation. For Z = X + Y or X - Y, absolute errors add: Delta_Z = Delta_X + Delta_Y.

THCB product and quotient propagation. For Z = X*Y or X/Y, relative errors add: delta_Z = delta_X + delta_Y.

THCB power propagation. For Z = X^n, relative error delta_Z = abs(n)*delta_X.

THCB resistance measurement. R = U/I and delta_R = delta_U + delta_I. Then Delta_R = R*delta_R.

THCB power measurement. P = U*I and delta_P = delta_U + delta_I.

THCB density measurement. rho = m/V, so delta_rho = delta_m + delta_V.

THCB area from length. If A = l^2, then delta_A = 2*delta_l.

THCB volume from length. If V = l^3, then delta_V = 3*delta_l.

THCB rounding. Keep enough intermediate precision, then round final error and value consistently with the error magnitude.

THCB percentage trap. If delta = 0.02, percentage error is 2%, not 0.02%.

THCB unit conversion. If length readings are in mm and final result is in m, convert both value and absolute error to m.

THCB instrument examples. A ruler with 1 mm smallest division has Delta_instrument = 1 mm in this dataset.

THCB if true value is given, absolute error can be abs(measured - true). If repeated values are given, use mean and random error.

THCB if multiple instruments contribute to a derived quantity, propagate each relative or absolute error according to the formula.

THCB if asked maximum absolute error, use the maximum allowed deviation, not standard deviation.

THCB if asked average absolute error explicitly, follow wording, but dataset baseline often expects max deviation for random error.

THCB if measured value is zero, relative error is undefined; answer qualitatively or use absolute error only.

THCB answer_type is quantitative for error calculations and qualitative when asking which measurement is more precise.

THCB precision comparison. Smaller relative error means more precise measurement, even if absolute error is larger.

THCB final sanity check: errors are nonnegative. A negative Delta is always wrong.
