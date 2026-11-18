"""
recommender.py
Adds plain-language explanations and recommendations to the risk analysis.
"""

DISCLAIMER = (
    "This is an automated analysis that points out possible risks. "
    "It is not legal advice."
)

ESCALATION_NOTE = (
    "The wording of this clause (for example 'without notice' or 'sole discretion') "
    "makes it more serious than usual."
)

GUIDANCE = {
    "Data Sharing": {
        "explanation": "The company can pass your personal information to other companies, such as partners or advertisers.",
        "recommendation": "Check your privacy settings and opt out of data sharing if the service allows it. Share only the information you really need to.",
    },
    "Auto Renewal": {
        "explanation": "Your subscription continues automatically and you are charged again unless you cancel in time.",
        "recommendation": "Note the renewal date, set a reminder, and turn off auto-renewal if you do not want to continue.",
    },
    "No Refund Policy": {
        "explanation": "Once you pay, you may not be able to get your money back, even if you change your mind.",
        "recommendation": "Be sure about the purchase before paying. Look for a trial period or a money-back guarantee first.",
    },
    "Liability Limitation": {
        "explanation": "The company limits or denies responsibility if something goes wrong, such as data loss or damage.",
        "recommendation": "Keep your own backups of anything important and avoid depending on the service for critical needs.",
    },
    "Arbitration Clause": {
        "explanation": "You may have to settle disputes through private arbitration instead of going to court, and you may give up the right to a class action.",
        "recommendation": "Understand that your legal options are limited. Check whether the service lets you opt out of arbitration within a set time.",
    },
    "Account Termination": {
        "explanation": "The company can suspend or close your account, and in some cases do so without telling you first.",
        "recommendation": "Keep a copy of your important data and content outside the service in case your access is removed.",
    },
    "Data Retention": {
        "explanation": "The company may keep your data for a long time, even after you stop using the service or delete your account.",
        "recommendation": "Look for a way to request deletion of your data, and avoid uploading sensitive information you would not want stored.",
    },
    "Location Tracking": {
        "explanation": "The app can collect where you are, sometimes even while you are not using it.",
        "recommendation": "Set location access to 'while using the app' or turn it off in your phone settings if the app works without it.",
    },
    "Marketing Consent": {
        "explanation": "You agree to receive promotions, and your information may be used to show you targeted ads.",
        "recommendation": "Untick marketing options when signing up, and use the unsubscribe link or settings page to opt out.",
    },
    "Policy Change Without Notice": {
        "explanation": "The company can change the terms at any time, and it may not tell you when it does.",
        "recommendation": "Review the terms again from time to time, and keep a copy of the version you originally agreed to.",
    },
}

DEFAULT_GUIDANCE = {
    "explanation": "This clause may affect your rights or your data.",
    "recommendation": "Read this clause carefully before accepting.",
}

LEVEL_TEXT = {
    "Low": (
        "This document looks fairly safe overall.",
        "Still read the flagged clauses once before you accept.",
    ),
    "Medium": (
        "This document has some conditions you should know about.",
        "Read the flagged clauses carefully and adjust your settings where possible before accepting.",
    ),
    "High": (
        "This document has several serious conditions.",
        "Think carefully before accepting. If you do accept, limit the personal data you share and review the High severity clauses first.",
    ),
}


def get_guidance(category, escalated=False):
    """Return (explanation, recommendation) for one flagged clause."""
    info = GUIDANCE.get(category, DEFAULT_GUIDANCE)
    explanation = info["explanation"]
    if escalated:
        explanation += " " + ESCALATION_NOTE
    return explanation, info["recommendation"]


def overall_summary(result):
    """Short paragraph describing the whole document."""
    flagged = result["flagged"]
    if not flagged:
        return "No risky clauses were detected in this document. You may still want to skim it yourself."

    opening, _ = LEVEL_TEXT[result["level"]]
    text = f"{opening} We found {len(flagged)} potentially risky clauses out of {result['total_clauses']}."

    high_categories = []
    for item in flagged:
        if item["severity"] == "High" and item["category"] not in high_categories:
            high_categories.append(item["category"])
    if high_categories:
        text += " The most serious concerns are: " + ", ".join(high_categories) + "."
    return text


def add_guidance(result):
    """
    Main function used by the rest of the app.
    Adds explanation and recommendation to every flagged clause, and an
    overall summary, advice and disclaimer to the result.
    """
    for item in result["flagged"]:
        item["explanation"], item["recommendation"] = get_guidance(
            item["category"], item["escalated"]
        )

    result["summary"] = overall_summary(result)
    result["overall_advice"] = LEVEL_TEXT[result["level"]][1] if result["flagged"] else ""
    result["disclaimer"] = DISCLAIMER
    return result





