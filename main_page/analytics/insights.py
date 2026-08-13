def generate(context):
    """
    Generate executive AI insights for the Enterprise Dashboard.
    """

    insights = []

    # ----------------------------------------
    # Overall positive prediction rate
    # ----------------------------------------

    positive_rate = context.get("positive_rate", 0)

    if positive_rate >= 20:
        insights.append(
            "The overall positive prediction rate exceeds 20%, suggesting a relatively high-risk patient population."
        )
    elif positive_rate >= 10:
        insights.append(
            f"The overall positive prediction rate is {positive_rate}%, indicating a moderate population health risk."
        )
    else:
        insights.append(
            "The overall positive prediction rate remains low, indicating a generally healthy patient population."
        )

    # ----------------------------------------
    # High-risk patients
    # ----------------------------------------

    high_risk = context.get("high_risk_patients", [])

    if len(high_risk) >= 10:
        insights.append(
            f"{len(high_risk)} high-risk patients are currently prioritized for clinical review."
        )

    # ----------------------------------------
    # Clinic comparison
    # ----------------------------------------

    clinics = context.get("clinic_comparison", [])

    if clinics:

        highest = max(
            clinics,
            key=lambda clinic: clinic["positive_rate"],
        )

        insights.append(
            f"{highest['clinic']} currently has the highest positive prediction rate ({highest['positive_rate']}%)."
        )

    # ----------------------------------------
    # Historical dataset
    # ----------------------------------------

    total_predictions = context.get(
        "total_predictions",
        0,
    )

    if total_predictions >= 3000:

        insights.append(
            f"Historical analytics are generated from {total_predictions:,} AI prediction records spanning approximately 18 months."
        )

    return insights