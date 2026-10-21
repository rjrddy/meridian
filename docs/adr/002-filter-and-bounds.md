# Weighted observations and scalar Kalman state

Context: measurements have different noise and freshness, and sources can disappear.
Options: arithmetic mean, complementary filter, scalar Kalman random-walk model, general matrix EKF.
Decision: age-inflated inverse-variance measurement fusion followed by a scalar Kalman update. Finite bounded samples, positive finite variances, capped stream counts and buffer capacities protect numerical and memory limits.
Tradeoffs: understandable dynamics and explicit uncertainty. No velocity model, nonlinear modalities or calibration-uncertainty propagation. A held sample can be reused on successive ticks, so posterior variance is model confidence, not calibrated empirical coverage. Future work should model temporal correlation or consume observations once. RMSE is evaluated independently against synthetic truth.
