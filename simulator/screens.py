"""Screen definitions for TaxAct Simulator.

Each screen defines:
- elements: List of UI elements (buttons, checkboxes, textfields, labels)
- Each element has: type, image (for buttons), position, and action

Positions are based on actual TaxAct 2025 at 1920x1080 resolution.
"""

from typing import Any, Dict, List

# Button image base path (relative to .agents/screenshots/buttons/)
IMG_BASE = ".agents/screenshots/buttons"


def _btn(image: str, pos: tuple, next_screen: str = None, action: str = None) -> Dict[str, Any]:
    """Helper to create button element."""
    return {
        "type": "button",
        "image": image,
        "position": pos,
        "next_screen": next_screen,
        "action": action
    }


def _checkbox(checked_img: str, unchecked_img: str, pos: tuple, default_checked: bool = False) -> Dict[str, Any]:
    """Helper to create checkbox element."""
    return {
        "type": "checkbox",
        "image_checked": checked_img,
        "image_unchecked": unchecked_img,
        "position": pos,
        "checked": default_checked
    }


def _textfield(label_img: str, label_pos: tuple, field_offset: tuple = (150, 0),
               field_size: tuple = (200, 25), field_id: str = None) -> Dict[str, Any]:
    """Helper to create textfield element."""
    return {
        "type": "textfield",
        "label_image": label_img,
        "label_position": label_pos,
        "field_offset": field_offset,
        "field_size": field_size,
        "field_id": field_id,
        "value": ""
    }


def _label(text: str, pos: tuple, font_size: int = 14) -> Dict[str, Any]:
    """Helper to create text label."""
    return {
        "type": "label",
        "text": text,
        "position": pos,
        "font_size": font_size
    }


# =============================================================================
# FORM 1120 SCREENS (36 Steps)
# =============================================================================

SCREENS_1120: Dict[str, Dict[str, Any]] = {

    # -------------------------------------------------------------------------
    # Screen 0: Client Manager (Base/Start)
    # -------------------------------------------------------------------------
    "client_manager": {
        "title": "Client Manager",
        "elements": [
            _btn("common/efile_menu.png", (850, 45), next_screen="efile_popup"),
            _btn("common/clients_button.png", (50, 45)),  # Already on this screen
            {
                "type": "client_table",
                "position": (50, 145),
                "row_height": 25,
                "columns": ["Client Name", "Return Type", "Fed EF Status"],
                "column_widths": [250, 80, 100]
            }
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 1: E-File Popup (after clicking E-File menu)
    # -------------------------------------------------------------------------
    "efile_popup": {
        "title": "E-File Center",
        "is_popup": True,
        "elements": [
            _label("E-File Center", (400, 100), font_size=18),
            _btn("common/submit_electronic_filing.png", (400, 250), next_screen="filing_screen"),
            _btn("common/popup_close_x.png", (750, 80), next_screen="client_manager"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 2: Filing Screen (File Extension selection)
    # -------------------------------------------------------------------------
    "filing_screen": {
        "title": "Filing",
        "elements": [
            _label("What would you like to do?", (400, 150), font_size=16),
            _btn("common/file_extension_option_unchecked.png", (400, 250), action="select_extension"),
            _btn("common/continue_blue.png", (850, 650), next_screen="federal_extension"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 3: Federal Extension (Yes/No)
    # -------------------------------------------------------------------------
    "federal_extension": {
        "title": "Federal Extension",
        "elements": [
            _label("Would you like to file a Federal Extension?", (400, 200), font_size=16),
            _btn("common/yes_green.png", (400, 350), next_screen="form_7004_intro"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 4: Form 7004 Intro
    # -------------------------------------------------------------------------
    "form_7004_intro": {
        "title": "Form 7004 - Application for Extension",
        "elements": [
            _label("Form 7004 - Application for Automatic Extension", (400, 150), font_size=18),
            _btn("1120/complete_form_7004.png", (400, 350), next_screen="corporation_name"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 5: Corporation Name
    # -------------------------------------------------------------------------
    "corporation_name": {
        "title": "Corporation Name",
        "elements": [
            _label("Corporation Name", (400, 150), font_size=16),
            _label("SANDMEYER INC", (400, 250), font_size=14),  # From mock data
            _btn("common/continue_blue.png", (850, 650), next_screen="homeowners_assoc"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 6: Homeowners Association Checkbox
    # -------------------------------------------------------------------------
    "homeowners_assoc": {
        "title": "Homeowners Association",
        "elements": [
            _label("Is this a Homeowners Association?", (400, 200), font_size=16),
            _checkbox(
                "1120/checkbox_homeowners_checked.png",
                "1120/checkbox_homeowners_unchecked.png",
                (400, 300),
                default_checked=False
            ),
            _btn("common/continue_blue.png", (850, 650), next_screen="address"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 7: Address
    # -------------------------------------------------------------------------
    "address": {
        "title": "Address",
        "elements": [
            _label("Business Address", (400, 150), font_size=16),
            _label("123 Main Street, Chicago, IL 60601", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="federal_id"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 8: Federal ID Number
    # -------------------------------------------------------------------------
    "federal_id": {
        "title": "Federal ID Number",
        "elements": [
            _label("Employer Identification Number (EIN)", (400, 150), font_size=16),
            _label("12-3456789", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="fiscal_year"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 9: Fiscal Year
    # -------------------------------------------------------------------------
    "fiscal_year": {
        "title": "Fiscal Year",
        "elements": [
            _label("Tax Year", (400, 150), font_size=16),
            _label("Calendar Year 2025", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="todays_date"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 10: Today's Date
    # -------------------------------------------------------------------------
    "todays_date": {
        "title": "Today's Date",
        "elements": [
            _label("Today's Date", (400, 150), font_size=16),
            _label("02/10/2026", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="no_office_us"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 11: No Office in US Checkbox
    # -------------------------------------------------------------------------
    "no_office_us": {
        "title": "No Office in United States",
        "elements": [
            _label("No office or place of business in the United States?", (400, 200), font_size=16),
            _checkbox(
                "1120/checkbox_no_office_checked.png",
                "1120/checkbox_no_office_unchecked.png",
                (400, 300),
                default_checked=False
            ),
            _btn("common/continue_blue.png", (850, 650), next_screen="section_checkbox"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 12: Section 1.6081-5 Checkbox
    # -------------------------------------------------------------------------
    "section_checkbox": {
        "title": "Section 1.6081-5",
        "elements": [
            _label("Section 1.6081-5 Election?", (400, 200), font_size=16),
            _checkbox(
                "1120/checkbox_section_checked.png",
                "1120/checkbox_section_unchecked.png",
                (400, 300),
                default_checked=False
            ),
            _btn("common/continue_blue.png", (850, 650), next_screen="tax_liability"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 13: Tax Liability (Scrollable)
    # -------------------------------------------------------------------------
    "tax_liability": {
        "title": "Tax Liability and Payments",
        "scrollable": True,
        "scroll_to_reveal": "common/continue_blue.png",
        "elements": [
            _label("Tax Liability and Payments", (400, 150), font_size=16),
            _label("Estimated tax liability: $0", (400, 300), font_size=14),
            _label("Total payments: $0", (400, 350), font_size=14),
            _label("Balance due: $0", (400, 400), font_size=14),
            # Continue button is below the fold - requires scroll
            _btn("common/continue_blue.png", (850, 850), next_screen="payment_amount"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 14: Payment Amount
    # -------------------------------------------------------------------------
    "payment_amount": {
        "title": "Payment Amount",
        "elements": [
            _label("Payment Amount", (400, 150), font_size=16),
            _label("Amount to pay with extension: $0.00", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="print_form_7004"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 15: Print Form 7004
    # -------------------------------------------------------------------------
    "print_form_7004": {
        "title": "Print Form 7004",
        "elements": [
            _label("Form 7004 Ready", (400, 150), font_size=16),
            _btn("1120/efile_form_7004.png", (400, 350), next_screen="acknowledgment"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 16: Acknowledgment Status
    # -------------------------------------------------------------------------
    "acknowledgment": {
        "title": "Acknowledgment Status",
        "elements": [
            _label("Acknowledgment Status", (400, 150), font_size=16),
            _label("Pending submission...", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="signing_officer_info"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 17: Signing Officer Information (Textfields)
    # -------------------------------------------------------------------------
    "signing_officer_info": {
        "title": "Signing Officer Information",
        "elements": [
            _label("Signing Officer Information", (400, 100), font_size=18),
            _textfield("1120/label_title.png", (200, 200), field_id="officer_title"),
            _textfield("1120/label_email.png", (200, 260), field_offset=(150, 0),
                      field_size=(250, 25), field_id="officer_email"),
            _textfield("1120/label_phone.png", (200, 320), field_offset=(150, 0),
                      field_size=(150, 25), field_id="officer_phone"),
            _btn("common/continue_blue.png", (850, 650), next_screen="officer_signature"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 18: Officer's Signature (PIN Entry)
    # -------------------------------------------------------------------------
    "officer_signature": {
        "title": "Officer's Signature",
        "elements": [
            _label("Officer's Signature", (400, 100), font_size=18),
            _textfield("1120/label_pin.png", (200, 250), field_offset=(150, 0),
                      field_size=(100, 25), field_id="officer_pin"),
            _btn("common/continue_blue.png", (850, 650), next_screen="ero_signature"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 19: ERO Signature
    # -------------------------------------------------------------------------
    "ero_signature": {
        "title": "ERO Signature",
        "elements": [
            _label("ERO Signature", (400, 150), font_size=16),
            _label("Electronic Return Originator signature on file.", (400, 250), font_size=14),
            _btn("common/continue_blue.png", (850, 650), next_screen="federal_efile_alerts"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 20: Federal E-File Alerts
    # -------------------------------------------------------------------------
    "federal_efile_alerts": {
        "title": "Federal E-File Alerts",
        "elements": [
            _label("Federal E-File Alerts", (400, 150), font_size=16),
            _label("Run alerts to check for errors before submission.", (400, 250), font_size=14),
            _btn("1120/start_form_7004_alerts.png", (400, 400), next_screen="alerts_result"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 21a: Alerts Result - PASSED (Conditional)
    # -------------------------------------------------------------------------
    "alerts_result": {
        "title": "Alerts Result",
        "conditional": True,
        "condition_var": "alerts_passed",  # True = passed, False = error
        "elements_if_true": [
            _label("Alerts Result", (400, 150), font_size=16),
            {
                "type": "image",
                "image": "common/passed_alerts.png",
                "position": (400, 300)
            },
            _btn("common/continue_blue.png", (850, 650), next_screen="submit_efile"),
        ],
        "elements_if_false": [
            _label("Alerts Result - Errors Found", (400, 150), font_size=16),
            _label("Error: Missing information", (400, 300), font_size=14),
            _btn("common/clients_button.png", (50, 45), next_screen="client_manager"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 22: Submit E-File
    # -------------------------------------------------------------------------
    "submit_efile": {
        "title": "Submit E-File",
        "elements": [
            _label("Ready to Submit", (400, 150), font_size=16),
            _label("Click Submit to file your extension.", (400, 250), font_size=14),
            _btn("1120/submit_efile.png", (400, 400), next_screen="confirmation"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 23: Confirmation (Green Continue)
    # -------------------------------------------------------------------------
    "confirmation": {
        "title": "Confirmation",
        "elements": [
            _label("Extension Submitted Successfully!", (400, 200), font_size=18),
            _label("Your Form 7004 has been submitted.", (400, 300), font_size=14),
            _btn("common/continue_green.png", (850, 650), next_screen="filing_complete"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 24: Filing Complete
    # -------------------------------------------------------------------------
    "filing_complete": {
        "title": "Filing Complete",
        "elements": [
            _label("Filing Complete", (400, 150), font_size=18),
            _label("What would you like to do next?", (400, 250), font_size=14),
            _btn("common/new_return.png", (400, 400), next_screen="add_client_popup"),
        ]
    },

    # -------------------------------------------------------------------------
    # Screen 25: Add Client Popup
    # -------------------------------------------------------------------------
    "add_client_popup": {
        "title": "Add Client",
        "is_popup": True,
        "elements": [
            _label("Add New Client", (400, 150), font_size=16),
            _btn("common/popup_close_x.png", (750, 100), next_screen="client_manager"),
        ]
    },
}


# =============================================================================
# FORM 1120S SCREENS (Placeholder - to be filled)
# =============================================================================

SCREENS_1120S: Dict[str, Dict[str, Any]] = {
    # 1120S has different screens - will be defined based on actual process
    "client_manager": SCREENS_1120["client_manager"],  # Same as 1120
    # ... additional 1120S-specific screens
}


def get_screens(return_type: str) -> Dict[str, Dict[str, Any]]:
    """Get screen definitions for return type."""
    if return_type == "1120":
        return SCREENS_1120
    elif return_type == "1120S":
        return SCREENS_1120S
    else:
        raise ValueError(f"Unknown return type: {return_type}")
