import numpy as np
import pandas as pd
from typing import List
from sklearn.ensemble import IsolationForest
from app.core.logging import logger
from app.schemas.analytics import (
    AnomalyDetectRequest,
    AnomalyDetectResponse,
    AnomalyResultItem,
    ExpenseDataPoint
)

class AnalyticsService:
    """
    Spending analytics and anomaly detection.
    Uses Isolation Forest with scikit-learn when sufficient historical data exists (>= 10 points),
    and statistical baseline (IQR / Z-score) otherwise.
    Never fabricates fraud labels; marks items honestly as NORMAL, UNUSUAL, or REQUIRES_REVIEW.
    """

    def detect_anomalies(self, req: AnomalyDetectRequest) -> AnomalyDetectResponse:
        expenses = req.historical_expenses
        count = len(expenses)

        # Baseline case: Insufficient data
        if count < 5:
            results = [
                AnomalyResultItem(
                    expense_id=exp.expense_id,
                    amount=exp.amount,
                    status="INSUFFICIENT_DATA",
                    anomaly_score=0.0,
                    reason="Insufficient historical transactions in group (minimum 5 required for statistical baseline)."
                )
                for exp in expenses
            ]
            return AnomalyDetectResponse(
                results=results,
                method_used="INSUFFICIENT_DATA",
                historical_count=count,
                mean_amount=float(np.mean([float(e.amount) for e in expenses])) if count > 0 else 0.0,
                std_amount=0.0
            )

        amounts = np.array([float(e.amount) for e in expenses])
        mean_amt = float(np.mean(amounts))
        std_amt = float(np.std(amounts))

        # Branch 1: If 5 <= count < 10, use statistical IQR & Z-score baseline
        if count < 10:
            return self._statistical_iqr_detection(expenses, amounts, mean_amt, std_amt)

        # Branch 2: Count >= 10, use Scikit-learn Isolation Forest with statistical features
        return self._isolation_forest_detection(expenses, amounts, mean_amt, std_amt)

    def _statistical_iqr_detection(
        self,
        expenses: List[ExpenseDataPoint],
        amounts: np.ndarray,
        mean_amt: float,
        std_amt: float
    ) -> AnomalyDetectResponse:
        q25 = float(np.percentile(amounts, 25))
        q75 = float(np.percentile(amounts, 75))
        iqr = q75 - q25
        upper_bound = q75 + 1.5 * iqr
        upper_extreme = q75 + 3.0 * iqr

        results: List[AnomalyResultItem] = []
        for exp in expenses:
            amt = float(exp.amount)
            if amt > upper_extreme and amt > mean_amt * 2.5:
                status = "REQUIRES_REVIEW"
                score = min(1.0, (amt - mean_amt) / (std_amt + 1e-5))
                reason = f"Significantly higher than typical group spending (IQR upper bound ₹{upper_bound:.2f})."
            elif amt > upper_bound and amt > mean_amt * 1.8:
                status = "UNUSUAL"
                score = min(0.8, (amt - mean_amt) / (std_amt + 1e-5))
                reason = f"Higher than normal group expense (average: ₹{mean_amt:.2f})."
            else:
                status = "NORMAL"
                score = 0.1
                reason = "Within normal group spending variation."

            results.append(AnomalyResultItem(
                expense_id=exp.expense_id,
                amount=exp.amount,
                status=status,
                anomaly_score=round(score, 3),
                reason=reason
            ))

        return AnomalyDetectResponse(
            results=results,
            method_used="STATISTICAL_IQR",
            historical_count=len(expenses),
            mean_amount=round(mean_amt, 2),
            std_amount=round(std_amt, 2)
        )

    def _isolation_forest_detection(
        self,
        expenses: List[ExpenseDataPoint],
        amounts: np.ndarray,
        mean_amt: float,
        std_amt: float
    ) -> AnomalyDetectResponse:
        # Build feature matrix:
        # 1. raw amount
        # 2. ratio to mean
        # 3. z-score
        ratios = amounts / (mean_amt + 1e-5)
        z_scores = (amounts - mean_amt) / (std_amt + 1e-5)
        X = np.column_stack([amounts, ratios, z_scores])

        # Fit lightweight IsolationForest (low tree count to conserve CPU/RAM on 6GB machine)
        clf = IsolationForest(
            n_estimators=30,
            contamination=0.1,
            random_state=42
        )
        clf.fit(X)
        scores = -clf.decision_function(X) # Higher score = more anomalous
        preds = clf.predict(X) # -1 for anomaly, 1 for inlier

        results: List[AnomalyResultItem] = []
        for i, exp in enumerate(expenses):
            amt = float(exp.amount)
            raw_score = float(scores[i])
            is_anomaly = preds[i] == -1

            if is_anomaly and amt > mean_amt * 2.5:
                status = "REQUIRES_REVIEW"
                reason = f"Transaction amount ₹{amt:.2f} is significantly deviated from group patterns (average ₹{mean_amt:.2f})."
            elif (is_anomaly and amt > mean_amt * 1.8) or (amt > mean_amt * 2.5):
                status = "UNUSUAL"
                reason = f"Unusually high compared to historical pattern (group average: ₹{mean_amt:.2f})."
            else:
                status = "NORMAL"
                reason = "Consistent with normal group spending patterns."

            results.append(AnomalyResultItem(
                expense_id=exp.expense_id,
                amount=exp.amount,
                status=status,
                anomaly_score=round(float(np.clip(raw_score + 0.5, 0.0, 1.0)), 3),
                reason=reason
            ))

        return AnomalyDetectResponse(
            results=results,
            method_used="ISOLATION_FOREST",
            historical_count=len(expenses),
            mean_amount=round(mean_amt, 2),
            std_amount=round(std_amt, 2)
        )

analytics_service = AnalyticsService()
