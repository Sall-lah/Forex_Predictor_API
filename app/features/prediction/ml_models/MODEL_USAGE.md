### How to Load and Use the Saved Model

To load the previously saved LightGBM model (`lightgbm_model_forex.pkl`) and make predictions, you can use the `joblib` library.

#### 1. Load the Model

```python
import joblib
import pandas as pd

# Load the saved model
loaded_model = joblib.load('lightgbm_model_forex.pkl')
print("Model loaded successfully!")
```

#### 2. Model Input Parameters (Features)

The loaded model expects input data in a pandas DataFrame format with the same 63 features used during training. These features are derived from the OHLCV data after feature extraction, labeling, and dropping the original 'open', 'high', 'low', 'close', 'labels', and 'asset' columns. The order of columns is important.

The features expected by the model are:

```python
# Example of how to prepare new data for prediction
# 'new_data' should be a DataFrame with the exact same columns and order as X_train_features or X_test_features.

# You can inspect the required feature names from X_train_features
required_features = X_train_features.columns.tolist()
print("Required features for prediction:")
print(required_features)

# Create a dummy DataFrame with the expected columns for demonstration
# In a real scenario, you would generate these features from new OHLCV data
# using the `extract_ohlcv_features` and `drop_ohlc_columns` functions.

# Example of a new data point (replace with actual feature calculations)
dummy_data = pd.DataFrame(columns=required_features)
# Add a row of dummy values (e.g., all zeros or representative values)
dummy_data.loc[0] = [0.0] * len(required_features)

# Make predictions
# For multiclass classification (Hold: 0, Buy: 1, Sell: 2),
# predict_proba gives the probability for each class in the order of class labels.
predictions_proba = loaded_model.predict_proba(dummy_data)
print(f"Predicted probabilities for dummy data: {predictions_proba}")

# To interpret the probabilities:
# predictions_proba[0][0] is the probability of 'Hold' (class 0)
# predictions_proba[0][1] is the probability of 'Buy' (class 1)
# predictions_proba[0][2] is the probability of 'Sell' (class 2)

print(f"Probability of Hold: {predictions_proba[0][0]:.4f}")
print(f"Probability of Buy: {predictions_proba[0][1]:.4f}")
print(f"Probability of Sell: {predictions_proba[0][2]:.4f}")

# predict gives the class label (0, 1, or 2)
predictions = loaded_model.predict(dummy_data)
print(f"Predicted class for dummy data: {predictions}")

# Map the predicted class label to its meaning
class_mapping = {0: 'Hold', 1: 'Buy', 2: 'Sell'}
predicted_action = class_mapping[predictions[0]]
print(f"Predicted action for dummy data: {predicted_action}")
```

**Key steps for preparing new data for prediction:**

1.  **Resample OHLCV data:** Ensure your raw OHLCV data is resampled to hourly intervals, similar to `load_and_preprocess` function.
2.  **Extract Features:** Apply the `extract_ohlcv_features` function to your new OHLCV data.
3.  **Drop OHLC Columns:** Use the `drop_ohlc_columns` function to remove 'open', 'high', 'low', 'close' from the feature set.
4.  **Align Columns:** Ensure the resulting DataFrame has the exact same columns and in the same order as `X_train_features` before passing it to `loaded_model.predict()` or `loaded_model.predict_proba()`.