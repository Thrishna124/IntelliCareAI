LUNG_CANCER_RECOMMENDATIONS = {

    "Very Low": {
        "status": (
            "The AI model indicates a very low likelihood of a "
            "malignant lung finding."
        ),
        "recommendations": [
            "Continue routine health monitoring.",
            "Avoid smoking and exposure to second-hand smoke.",
            "Avoid prolonged exposure to dust, fumes, and other respiratory irritants.",
            "Follow recommended routine health screenings."
        ],
    },

    "Low": {
        "status": (
            "The AI model indicates a low likelihood of a "
            "malignant lung finding."
        ),
        "recommendations": [
            "Continue routine health monitoring and recommended screening.",
            "Avoid smoking and second-hand smoke.",
            "Minimize exposure to occupational and environmental respiratory irritants.",
            "Discuss any persistent respiratory symptoms with a healthcare professional."
        ],
    },

    "Borderline": {
        "status": (
            "The AI model indicates an intermediate likelihood of a "
            "malignant lung finding and further clinical assessment "
            "may be appropriate."
        ),
        "recommendations": [
            "Discuss the result with a qualified healthcare professional.",
            "Further imaging or clinical evaluation may be recommended.",
            "Avoid smoking and exposure to respiratory irritants.",
            "Report persistent cough, chest discomfort, unexplained weight loss, or breathing difficulties to your healthcare provider."
        ],
    },

    "Moderate": {
        "status": (
            "The AI model indicates a moderate likelihood of a "
            "malignant lung finding and clinical follow-up is recommended."
        ),
        "recommendations": [
            "Arrange clinical evaluation with a qualified healthcare professional.",
            "Discuss whether additional imaging or diagnostic testing is appropriate.",
            "Avoid smoking and exposure to respiratory irritants.",
            "Follow the healthcare professional's recommendations for further evaluation."
        ],
    },

    "High": {
        "status": (
            "The AI model indicates a high likelihood of a "
            "malignant lung finding and prompt clinical evaluation "
            "is recommended."
        ),
        "recommendations": [
            "Seek prompt evaluation from a qualified healthcare professional.",
            "Discuss appropriate diagnostic imaging and further evaluation.",
            "Do not rely on the AI result as a definitive diagnosis.",
            "Avoid smoking and exposure to respiratory irritants.",
            "Follow all recommendations provided by your healthcare professional."
        ],
    },
}