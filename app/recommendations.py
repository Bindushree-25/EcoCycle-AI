
"""Transparent, conservative guidance for common electronic-waste categories."""

GUIDANCE = {
    "battery": {
        "title": "Battery",
        "summary": "Keep batteries out of household rubbish and ordinary recycling bins.",
        "steps": [
            "Keep the battery dry and away from heat, flames, and metal objects.",
            "For removable lithium batteries, protect exposed terminals with non-conductive tape if local guidance allows.",
            "Do not puncture, crush, open, or attempt to repair a swollen, leaking, or damaged battery.",
            "Use a collection point that explicitly accepts this battery type."
        ],
        "route": "specialist_recycling",
        "caution": "Never puncture, crush, or dismantle a battery. If hot, swollen, hissing, leaking, or smoking, do not handle it. Move away and contact local emergency or hazardous-waste services."
    },
    "keyboard": {
        "title": "Keyboard",
        "summary": "A working keyboard may be reusable; otherwise send it to an electronics collection stream.",
        "steps": [
            "Test it and clean the exterior without soaking electronics.",
            "If working, consider donation or resale after checking condition.",
            "If not working, use an e-waste collection point; do not put it in mixed recycling."
        ],
        "route": "reuse_or_recycle",
        "caution": "Do not dismantle components unless trained and equipped to do so."
    },
    "microwave": {
        "title": "Microwave",
        "summary": "Microwave ovens contain electrical components and should be handled by an appropriate e-waste service.",
        "steps": [
            "Unplug the appliance and keep it dry.",
            "If it works, consider repair or resale through a qualified service.",
            "Arrange collection with an authorized e-waste or appliance recycler."
        ],
        "route": "specialist_recycling",
        "caution": "Do not open the casing. Internal components can retain dangerous voltages even after unplugging."
    },
    "mobile": {
        "title": "Mobile phone",
        "summary": "Phones can often be repaired, reused, traded in, or recycled through electronics take-back services.",
        "steps": [
            "Back up data, sign out of accounts, remove SIM and memory cards, and factory-reset the phone.",
            "If the device is working, compare repair, trade-in, donation, or resale options.",
            "If the battery is damaged or swollen, do not charge or ship it normally; ask the receiving service for safe handling instructions."
        ],
        "route": "reuse_or_recycle",
        "caution": "Do not puncture or remove a built-in battery unless qualified to do so."
    },
    "mouse": {
        "title": "Computer mouse",
        "summary": "A working mouse can be reused; a broken one belongs in an electronics collection stream.",
        "steps": [
            "Remove replaceable batteries and route them separately.",
            "Test the mouse and consider reuse if it works.",
            "Take non-working equipment to an e-waste collection point."
        ],
        "route": "reuse_or_recycle",
        "caution": "Do not put electronic accessories in ordinary mixed recycling unless your local program explicitly accepts them."
    },
    "pcb": {
        "title": "Printed circuit board",
        "summary": "Circuit boards contain mixed materials and should go to a specialist electronics recycler.",
        "steps": [
            "Keep the board intact and avoid creating dust.",
            "Store it away from children, pets, food, and moisture.",
            "Use a recycler that accepts circuit boards and can recover materials safely."
        ],
        "route": "specialist_recycling",
        "caution": "Do not burn boards, use acids, or dismantle them using improvised methods."
    },
    "player": {
        "title": "Media player",
        "summary": "Small electronics may be suitable for reuse, repair, or electronics recycling.",
        "steps": [
            "Check whether it works and whether accessories are included.",
            "Erase personal data if it stores any.",
            "Use a repair, donation, resale, or e-waste collection route based on condition."
        ],
        "route": "reuse_or_recycle",
        "caution": "Remove batteries only if they are designed to be user-removable and can be handled safely."
    },
    "printer": {
        "title": "Printer",
        "summary": "Printers may contain toner or ink and should be sent through an appropriate take-back or e-waste service.",
        "steps": [
            "Unplug it and follow the manufacturer's instructions for removing ink or toner cartridges.",
            "Check whether the manufacturer or retailer offers a take-back program.",
            "Use a collection service that accepts printers and their consumables."
        ],
        "route": "specialist_recycling",
        "caution": "Avoid breathing toner dust; do not dismantle power components."
    },
    "television": {
        "title": "Television",
        "summary": "Televisions require an electronics or appliance recycling route, not ordinary household bins.",
        "steps": [
            "Keep the screen protected during transport.",
            "Check retailer take-back or authorized e-waste collection options.",
            "Arrange bulky-item collection if you cannot transport it safely."
        ],
        "route": "specialist_recycling",
        "caution": "Do not break the screen or open the casing; older display types may contain hazardous materials."
    },
    "washing_machine": {
        "title": "Washing machine",
        "summary": "Large appliances are often repairable and should be collected by an appliance service or recycler.",
        "steps": [
            "If safe and practical, unplug it and disconnect water according to the manual.",
            "Check repair options before replacing a working appliance.",
            "Arrange retailer take-back, municipal bulky collection, or an authorized appliance recycler."
        ],
        "route": "repair_or_recycle",
        "caution": "Use appropriate lifting and disconnection help; do not dismantle electrical or refrigerant-containing equipment."
    }
}

ALIASES = {
    "battery": "battery", "batteries": "battery",
    "keyboard": "keyboard", "microwave": "microwave",
    "mobile": "mobile", "phone": "mobile", "mobile phone": "mobile",
    "mouse": "mouse", "pcb": "pcb", "circuit board": "pcb",
    "player": "player", "media player": "player",
    "printer": "printer", "television": "television", "tv": "television",
    "washing machine": "washing_machine", "washing_machine": "washing_machine"
}


def get_guidance(category):
    key = ALIASES.get((category or "").strip().lower())
    if not key:
        return {
            "title": "General electronic waste",
            "summary": "Choose a reuse, repair, take-back, or authorized e-waste collection route.",
            "steps": [
                "Do not place electronic equipment in household rubbish or mixed recycling by default.",
                "If it stores personal data, back it up and securely erase it before transfer.",
                "Keep damaged batteries and broken components separate and ask the receiving service how to handle them."
            ],
            "route": "check_local_rules",
            "caution": "Do not dismantle equipment or handle leaking, swollen, hot, or smoking batteries."
        }
    return GUIDANCE[key]
