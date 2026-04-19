@'
---
status: complete
---
# Quick Task: Update prediction api request. remove asset and lock interval to 60. only request for the asset pair

1. Update pi/app/features/prediction/schemas.py to remove sset and interval from PredictionRequest and remove sset from PredictionResponse.
2. Update pi/app/features/prediction/service.py to remove the sset parameter from extract_features and hardcode interval=60 in the KrakenAPIClient.fetch_ohlcv_data call.
3. Update tests in pi/tests/features/prediction to match the new request and response schemas.
'@

