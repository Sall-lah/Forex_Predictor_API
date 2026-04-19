@'
---
status: complete
---
# Quick Task: Update prediction api request. remove asset and lock interval to 60. only request for the asset pair

Completed removing sset and interval from PredictionRequest schema. Now the request only takes pair.
interval is locked to 60 in pi/app/features/prediction/service.py where etch_ohlcv_data is called.
Tests were updated to match.
'@

