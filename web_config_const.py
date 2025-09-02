#!/usr/bin/env python3
"""
Configuration constants for Xray Monitor Web Interface
Customize these values according to your needs
"""

# ====================
# SERVER CONFIGURATION
# ====================

# Web server settings
WEB_SERVER = {
    "host": "127.0.0.1",  # Server host address
    "port": 8080,         # Server port
}

# Auto refresh interval (seconds)
AUTO_REFRESH_INTERVAL = 10

# ====================
# DELAY CATEGORIES
# ====================

# Define delay thresholds for quality categories (in milliseconds)
DELAY_CATEGORIES = {
    "EXCELLENT": {
        "max_delay": 600,
        "color": "GREEN_400",
        "quality_text": "Excellent",
        "signal_icon": "SIGNAL_CELLULAR_ALT",
        "signal_bars": 4
    },
    "GOOD": {
        "max_delay": 1000,
        "color": "BLUE_400",
        "quality_text": "Good",
        "signal_icon": "SIGNAL_CELLULAR_ALT_2_BAR",
        "signal_bars": 3
    },
    "FAIR": {
        "max_delay": 1200,
        "color": "ORANGE_400",
        "quality_text": "Fair",
        "signal_icon": "SIGNAL_CELLULAR_ALT_1_BAR",
        "signal_bars": 2
    },
    "POOR": {
        "max_delay": 9999,  # Anything above FAIR threshold
        "color": "YELLOW_700",
        "quality_text": "Poor",
        "signal_icon": "SIGNAL_CELLULAR_0_BAR",
        "signal_bars": 1
    },
    "OFFLINE": {
        "max_delay": 9999,
        "color": "RED_400",
        "quality_text": "Offline",
        "signal_icon": "SIGNAL_CELLULAR_OFF",
        "signal_bars": 0
    }
}

# ====================
# UI CONFIGURATION
# ====================

# Mobile breakpoint (pixels)
MOBILE_BREAKPOINT = 768

# Desktop grid configuration
DESKTOP_GRID = {
    "columns": 4,           # Number of columns in grid
    "max_card_width": 350,   # Maximum card width in pixels
    "card_aspect_ratio": 1.2,
    "spacing": 20,
    "padding": 30
}

# Mobile configuration
MOBILE_CONFIG = {
    "header_padding": 15,
    "content_padding": 10,
    "card_spacing": 10,
    "stat_card_width": 80,
    "search_height": 45,
    "dropdown_width": 100
}

# ====================
# THEME CONFIGURATION
# ====================

# Dark theme colors
DARK_THEME = {
    "primary": "BLUE_400",
    "primary_container": "BLUE_900",
    "secondary": "CYAN_400",
    "background": "GREY_900",
    "surface": "GREY_800",
    "on_primary": "WHITE",
    "on_secondary": "WHITE",
    "on_background": "WHITE",
    "on_surface": "WHITE",
}

# Light theme colors
LIGHT_THEME = {
    "primary": "BLUE_600",
    "primary_container": "BLUE_100",
    "secondary": "CYAN_600",
    "background": "GREY_100",
    "surface": "WHITE",
    "on_primary": "WHITE",
    "on_secondary": "WHITE",
    "on_background": "BLACK",
    "on_surface": "BLACK",
}

# Header gradient colors
HEADER_GRADIENT = {
    "start_color": "BLUE_900",
    "end_color": "PURPLE_900"
}

# ====================
# FILE PATHS
# ====================

PATHS = {
    "results_file": "./ping_results.json",
    "config_list": "./configs/config_list.json",
}

# ====================
# STATISTICS CARDS
# ====================

STAT_CARDS = {
    "total": {
        "title": "Total Configs",
        "title_mobile": "Total",
        "icon": "DNS",
        "color": "BLUE_400"
    },
    "online": {
        "title": "Online",
        "title_mobile": "Online",
        "icon": "CHECK_CIRCLE",
        "color": "GREEN_400"
    },
    "offline": {
        "title": "Offline",
        "title_mobile": "Offline",
        "icon": "ERROR",
        "color": "RED_400"
    },
    "average": {
        "title": "Avg Delay",
        "title_mobile": "Avg",
        "icon": "SPEED",
        "color": "ORANGE_400"
    }
}

# ====================
# SORT OPTIONS
# ====================

SORT_OPTIONS = {
    "desktop": [
        {"value": "name", "label": "Name"},
        {"value": "delay", "label": "Delay (Low to High)"},
        {"value": "delay_desc", "label": "Delay (High to Low)"},
        {"value": "status", "label": "Status"},
    ],
    "mobile": [
        {"value": "delay", "label": "Delay ↑"},
        {"value": "delay_desc", "label": "Delay ↓"},
        {"value": "name", "label": "Name"},
        {"value": "status", "label": "Status"},
    ]
}

# ====================
# TEXT CONFIGURATION
# ====================

TEXT = {
    "app_title": "XrayPulse",
    "app_title_full": "XrayPulse",
    "app_subtitle": "Real-time Configuration Performance Monitoring",
    "app_subtitle_mobile": "Configuration Monitor",
    "no_data_title": "No Data Available",
    "no_data_message": "Waiting for test results...",
    "error_title": "Error Loading Data",
    "search_placeholder": "Search configurations...",
    "search_placeholder_mobile": "Search...",
    "theme_tooltip": "Toggle Theme",
    "live_indicator": "Live"
}

# ====================
# ANIMATION SETTINGS
# ====================

ANIMATIONS = {
    "card_hover_duration": 300,
    "live_indicator_duration": 1000,
    "enable_mobile_animations": False,  # Disable heavy animations on mobile
}

# ====================
# ADVANCED SETTINGS
# ====================

ADVANCED = {
    "max_config_name_length": 30,        # Truncate config names longer than this
    "max_config_name_length_mobile": 35, # Truncate length for mobile
    "offline_delay_threshold": 9999,     # Delay value to consider as offline
    "progress_bar_max_delay": 1000,      # Maximum delay for progress bar calculation
    "enable_hover_effects": True,        # Enable hover effects on desktop
    "show_tooltips": True,               # Show tooltips on desktop
}