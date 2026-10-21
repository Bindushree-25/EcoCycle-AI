# Data and model artifacts

The provided `eco(3).zip` archive did not contain a dataset directory or trained e-waste model weights. Keep datasets and model artifacts outside the source package unless you have the right to redistribute them and the archive size remains reasonable.

Expected optional model path:
- `models/ewaste_mobilenet.h5`

The adapter expects ten output classes. Confirm class order and preprocessing from the original training code. Do not use the application’s model endpoint for real predictions until a compatible model is supplied and validated.

If recreating training, document dataset source/license, class counts, split strategy, random seed, preprocessing, model architecture, per-class metrics, confusion matrix, and held-out evaluation results. Do not report metrics from training accuracy alone.
