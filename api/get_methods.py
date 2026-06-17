import inspect
from app.features.prediction.service import OHLCVPreprocessor
print([m[0] for m in inspect.getmembers(OHLCVPreprocessor, predicate=inspect.isroutine)])
