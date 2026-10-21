# Weighted observations and scalar Kalman state

Context: measurements have different noise and freshness, and sources can disappear.
Options: arithmetic mean, complementary filter, scalar Kalman random-walk model, general matrix EKF.
Decision: age-inflated inverse-variance measurement fusion followed by a scalar Kalman update. Finite bounded samples, positive finite variances, capped stream counts and buffer capacities protect numerical and memory limits.
Tradeoffs: understandable dynamics and explicit uncertainty. No velocity model, nonlinear modalities or calibration-uncertainty propagation. Each observation is consumed at most once for a measurement update; holding a fresh sample contributes source-health information but does not repeatedly shrink covariance. Posterior variance is model confidence, not calibrated empirical coverage. RMSE is evaluated independently against synthetic truth.
