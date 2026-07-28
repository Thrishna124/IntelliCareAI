def calculate_health_metrics(best_predictions):
    """
    Calculate dashboard statistics from the best prediction of each disease.
    """

    results = {
        "count_green": 0,
        "count_yellow": 0,
        "count_red": 0,
        "total_predictions": len(best_predictions),
        "health_score": 0,
        "health_percentage": 0,
    }

    for entry in best_predictions.values():

        prediction = entry["prediction"]

        prediction_result = prediction["prediction"].lower()

        diagnosis = (
            prediction["diagnosis"].lower()
            if prediction["diagnosis"]
            else None
        )

        if diagnosis is not None:

            if prediction_result == "no" and diagnosis in ["normal", "none"]:
                results["count_green"] += 1

            elif prediction_result == "no":
                results["count_yellow"] += 1

            elif prediction_result == "yes":
                results["count_red"] += 1

        else:

            if prediction_result == "no":
                results["count_green"] += 1
            else:
                results["count_red"] += 1

    # --------------------------------------------------
# Health Score
# --------------------------------------------------

    results["health_score"] = (
    results["count_green"]
    + (0.5 * results["count_yellow"])
)

# --------------------------------------------------
# Health Percentage
# --------------------------------------------------

    if results["total_predictions"] > 0:

        results["health_percentage"] = round(
        (results["health_score"] / results["total_predictions"]) * 100
    )

    else:

        results["health_percentage"] = 0

# --------------------------------------------------
# Overall Health Status
# --------------------------------------------------

    if results["health_percentage"] >= 90:

        results["health_status"] = "Excellent"

        results["status_color"] = "success"

    elif results["health_percentage"] >= 70:

        results["health_status"] = "Good"

        results["status_color"] = "primary"

    elif results["health_percentage"] >= 50:

        results["health_status"] = "Needs Attention"

        results["status_color"] = "warning"

    else:

        results["health_status"] = "High Risk"

        results["status_color"] = "danger"

    return results