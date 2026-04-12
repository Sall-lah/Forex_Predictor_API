# Requirements: Timeframe Interval Support

## Functional Requirements
- **FR1:** The `interval` parameter must be added to the relevant backend endpoints (likely `/historic-data/live` and `/prediction/predict`).
- **FR2:** Valid interval values should be explicitly validated: `[1, 5, 15, 30, 60, 240, 1440, 10080, 21600]`.
- **FR3:** The Kraken API client must pass the interval to the Kraken endpoint.
- **FR4:** Preprocessing/prediction models must accommodate the different intervals. Note: If the model is strictly trained on a 1-hour interval, the user needs to be notified or a specific behavior needs to be documented.
- **FR5:** Express BFF proxy must pass the parameter if required.

## Non-Functional Requirements
- **NFR1:** Maintain the current polling logic to prevent Kraken rate limiting.
- **NFR2:** Maintain type safety in Python via Pydantic.