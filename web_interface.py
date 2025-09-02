"""
Web Interface for Xray Config Monitor
Mobile-First Responsive Design
"""

import flet as ft
import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
from web_config_const import *

class MonitorDashboard:
    """Mobile-responsive monitoring dashboard using Flet"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.results_file = Path(PATHS.get("results_file", "./ping_results.json"))
        self.config_cards = {}
        self.update_timer = None
        self.is_mobile = False
        self.setup_page()
        self.detect_screen_size()
        self.create_ui()
        
    def setup_page(self):
        """Configure page settings"""
        self.page.title = TEXT.get("app_title", "Xray Monitor")
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        
        # Remove fixed window size for mobile responsiveness
        self.page.window.width = None
        self.page.window.height = None
        
        # Modern color scheme from config
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=getattr(ft.Colors, DARK_THEME["primary"]),
                primary_container=getattr(ft.Colors, DARK_THEME["primary_container"]),
                secondary=getattr(ft.Colors, DARK_THEME["secondary"]),
                background=getattr(ft.Colors, DARK_THEME["background"]),
                surface=getattr(ft.Colors, DARK_THEME["surface"]),
                on_primary=getattr(ft.Colors, DARK_THEME["on_primary"]),
                on_secondary=getattr(ft.Colors, DARK_THEME["on_secondary"]),
                on_background=getattr(ft.Colors, DARK_THEME["on_background"]),
                on_surface=getattr(ft.Colors, DARK_THEME["on_surface"]),
            )
        )
        
        # Add resize handler
        self.page.on_resize = self.on_page_resize
    
    def detect_screen_size(self):
        """Detect if we're on mobile based on screen width"""
        if self.page.width and self.page.width < MOBILE_BREAKPOINT:
            self.is_mobile = True
        else:
            self.is_mobile = False
    
    def get_delay_category(self, delay: float, status: str) -> Dict:
        """Get category info based on delay and status"""
        if status != "online":
            return DELAY_CATEGORIES["OFFLINE"]
        
        if delay < DELAY_CATEGORIES["EXCELLENT"]["max_delay"]:
            return DELAY_CATEGORIES["EXCELLENT"]
        elif delay < DELAY_CATEGORIES["GOOD"]["max_delay"]:
            return DELAY_CATEGORIES["GOOD"]
        elif delay < DELAY_CATEGORIES["FAIR"]["max_delay"]:
            return DELAY_CATEGORIES["FAIR"]
        else:
            return DELAY_CATEGORIES["POOR"]
    
    def on_page_resize(self, e):
        """Handle page resize events"""
        old_is_mobile = self.is_mobile
        self.detect_screen_size()
        
        # Rebuild UI if switching between mobile/desktop
        if old_is_mobile != self.is_mobile:
            self.page.controls.clear()
            self.create_ui()
            self.load_results()
    
    def create_ui(self):
        """Create responsive UI based on screen size"""
        if self.is_mobile:
            self.create_mobile_ui()
        else:
            self.create_desktop_ui()
    
    def create_mobile_ui(self):
        """Create mobile-optimized UI"""
        
        # Compact header for mobile
        self.header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MONITOR_HEART, size=24, color=ft.Colors.CYAN_400),
                    ft.Text(
                        TEXT["app_title"],
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE,
                        icon_size=20,
                        on_click=self.toggle_theme,
                        tooltip=TEXT["theme_tooltip"],
                        icon_color=ft.Colors.WHITE,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(
                    TEXT["app_subtitle_mobile"],
                    size=12,
                    color=ft.Colors.GREY_400
                ),
            ], spacing=5),
            padding=ft.padding.all(MOBILE_CONFIG["header_padding"]),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    getattr(ft.Colors, HEADER_GRADIENT["start_color"]),
                    getattr(ft.Colors, HEADER_GRADIENT["end_color"])
                ],
            ),
        )
        
        # Horizontal scrollable stats for mobile
        self.stats_row = ft.Row(
            [
                self.create_mobile_stat_card(
                    STAT_CARDS["total"]["title_mobile"], "0",
                    getattr(ft.Icons, STAT_CARDS["total"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["total"]["color"])
                ),
                self.create_mobile_stat_card(
                    STAT_CARDS["online"]["title_mobile"], "0",
                    getattr(ft.Icons, STAT_CARDS["online"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["online"]["color"])
                ),
                self.create_mobile_stat_card(
                    STAT_CARDS["offline"]["title_mobile"], "0",
                    getattr(ft.Icons, STAT_CARDS["offline"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["offline"]["color"])
                ),
                self.create_mobile_stat_card(
                    STAT_CARDS["average"]["title_mobile"], "0ms",
                    getattr(ft.Icons, STAT_CARDS["average"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["average"]["color"])
                ),
            ],
            scroll=ft.ScrollMode.HIDDEN,
            spacing=MOBILE_CONFIG["card_spacing"],
        )
        
        # Search bar for mobile
        self.search_field = ft.TextField(
            label=TEXT["search_placeholder_mobile"],
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            filled=True,
            fill_color=ft.Colors.GREY_800,
            dense=True,
            height=MOBILE_CONFIG["search_height"],
            expand=True,
            on_change=self.filter_configs,
        )
        
        # Sort dropdown for mobile
        self.sort_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(opt["value"], opt["label"])
                for opt in SORT_OPTIONS["mobile"]
            ],
            value="delay",
            width=MOBILE_CONFIG["dropdown_width"],
            dense=True,
            # height=MOBILE_CONFIG["search_height"],
            filled=True,
            fill_color=ft.Colors.GREY_800,
            border_radius=10,
            on_change=self.sort_configs,
        )
        
        # Configs list for mobile (single column)
        self.configs_container = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=10,
            expand=True,
        )
        
        # Main mobile layout
        self.main_content = ft.Column([
            self.header,
            ft.Container(
                content=self.stats_row,
                padding=ft.padding.all(10),
            ),
            ft.Container(
                content=ft.Row([
                    self.search_field,
                    self.sort_dropdown,
                ], spacing=10),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
            ),
            ft.Container(
                content=self.configs_container,
                padding=ft.padding.all(10),
                expand=True,
            ),
        ], spacing=0, expand=True)
        
        self.page.add(self.main_content)
        self.start_auto_refresh()
        self.load_results()
    
    def create_desktop_ui(self):
        """Create desktop UI (original design)"""
        
        # Desktop header
        self.header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.MONITOR_HEART, size=40, color=ft.Colors.CYAN_400),
                    ft.Column([
                        ft.Text(
                            TEXT["app_title_full"],
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        ft.Text(
                            TEXT["app_subtitle"],
                            size=14,
                            color=ft.Colors.GREY_400
                        ),
                    ], spacing=0),
                ], spacing=20),
                ft.Row([
                    self.create_status_indicator(),
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE,
                        icon_size=24,
                        on_click=self.toggle_theme,
                        tooltip=TEXT["theme_tooltip"],
                        icon_color=ft.Colors.WHITE,
                    ),
                ], spacing=10),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    getattr(ft.Colors, HEADER_GRADIENT["start_color"]),
                    getattr(ft.Colors, HEADER_GRADIENT["end_color"])
                ],
            ),
        )
        
        # Desktop stats
        self.stats_row = ft.Row(
            [
                self.create_stat_card(
                    STAT_CARDS["total"]["title"], "0",
                    getattr(ft.Icons, STAT_CARDS["total"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["total"]["color"])
                ),
                self.create_stat_card(
                    STAT_CARDS["online"]["title"], "0",
                    getattr(ft.Icons, STAT_CARDS["online"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["online"]["color"])
                ),
                self.create_stat_card(
                    STAT_CARDS["offline"]["title"], "0",
                    getattr(ft.Icons, STAT_CARDS["offline"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["offline"]["color"])
                ),
                self.create_stat_card(
                    STAT_CARDS["average"]["title"], "0ms",
                    getattr(ft.Icons, STAT_CARDS["average"]["icon"]),
                    getattr(ft.Colors, STAT_CARDS["average"]["color"])
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=20,
        )
        
        # Desktop search and filter
        self.search_field = ft.TextField(
            label=TEXT["search_placeholder"],
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            filled=True,
            fill_color=ft.Colors.GREY_800,
            expand=True,
            on_change=self.filter_configs,
        )
        
        self.sort_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(opt["value"], opt["label"])
                for opt in SORT_OPTIONS["desktop"]
            ],
            value="delay",
            width=200,
            filled=True,
            fill_color=ft.Colors.GREY_800,
            border_radius=10,
            on_change=self.sort_configs,
        )
        
        self.filter_bar = ft.Container(
            content=ft.Row([
                self.search_field,
                self.sort_dropdown,
            ], spacing=20),
            padding=ft.padding.symmetric(horizontal=30, vertical=10),
        )
        
        # Desktop grid view
        self.configs_grid = ft.GridView(
            expand=True,
            runs_count=DESKTOP_GRID["columns"],
            max_extent=DESKTOP_GRID["max_card_width"],
            child_aspect_ratio=DESKTOP_GRID["card_aspect_ratio"],
            spacing=DESKTOP_GRID["spacing"],
            run_spacing=DESKTOP_GRID["spacing"],
            padding=ft.padding.all(DESKTOP_GRID["padding"]),
        )
        
        # Desktop layout
        self.main_content = ft.Column([
            self.header,
            ft.Container(
                content=self.stats_row,
                padding=ft.padding.all(30),
            ),
            self.filter_bar,
            self.configs_grid,
        ], spacing=0, expand=True)
        
        self.page.add(self.main_content)
        self.start_auto_refresh()
        self.load_results()
    
    def create_mobile_stat_card(self, title: str, value: str, icon, color) -> ft.Container:
        """Create compact statistics card for mobile"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=20, color=color),
                ft.Text(
                    value,
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    title,
                    size=11,
                    color=ft.Colors.GREY_400,
                ),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(10),
            border_radius=10,
            width=MOBILE_CONFIG["stat_card_width"],
            bgcolor=ft.Colors.GREY_800,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    ft.Colors.with_opacity(0.05, color),
                    ft.Colors.with_opacity(0.02, color),
                ],
            ),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, color)),
        )
    
    def create_mobile_config_card(self, name: str, data: Dict) -> ft.Container:
        """Create mobile-optimized config card"""
        delay = data.get("delay", 9999)
        status = data.get("status", "unknown")
        timestamp = data.get("timestamp", "")
        
        # Get category info from config
        category = self.get_delay_category(delay, status)
        border_color = getattr(ft.Colors, category["color"])
        status_color = border_color
        quality = category["quality_text"]
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M")
        except:
            time_str = "N/A"
        
        # Truncate name based on config
        max_length = ADVANCED["max_config_name_length_mobile"]
        display_name = name[:max_length] + "..." if len(name) > max_length else name
        
        return ft.Container(
            content=ft.Row([
                # Status indicator
                ft.Container(
                    width=4,
                    height=60,
                    bgcolor=status_color,
                    border_radius=ft.border_radius.only(top_left=10, bottom_left=10),
                ),
                # Main content
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            display_name,
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Row([
                            ft.Container(
                                content=ft.Text(
                                    quality,
                                    size=11,
                                    color=ft.Colors.WHITE,
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                bgcolor=status_color,
                                border_radius=10,
                            ),
                            ft.Text(
                                f"{delay:.0f}ms" if delay < ADVANCED["offline_delay_threshold"] else "N/A",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=status_color,
                            ),
                            ft.Text(
                                time_str,
                                size=11,
                                color=ft.Colors.GREY_400,
                            ),
                        ], spacing=10),
                    ], spacing=5),
                    expand=True,
                    padding=ft.padding.all(10),
                ),
            ], spacing=0),
            bgcolor=ft.Colors.GREY_800,
            border_radius=10,
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, border_color)),
            margin=ft.margin.symmetric(horizontal=5),
        )
    
    def create_status_indicator(self) -> ft.Container:
        """Create a status indicator widget"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    width=12,
                    height=12,
                    border_radius=6,
                    bgcolor=ft.Colors.GREEN_400,
                    animate=ft.Animation(duration=1000, curve=ft.AnimationCurve.EASE_IN_OUT),
                ),
                ft.Text("Live", color=ft.Colors.GREEN_400, size=14),
            ], spacing=8),
            padding=ft.padding.all(10),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN_400),
        )
    
    def create_stat_card(self, title: str, value: str, icon: str, color: str) -> ft.Container:
        """Create desktop statistics card"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=24, color=color),
                    ft.Text(title, size=14, color=ft.Colors.GREY_400),
                ], alignment=ft.MainAxisAlignment.START),
                ft.Text(
                    value,
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
            ], spacing=10),
            padding=ft.padding.all(20),
            border_radius=15,
            bgcolor=ft.Colors.GREY_800,
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    ft.Colors.with_opacity(0.05, color),
                    ft.Colors.with_opacity(0.02, color),
                ],
            ),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, color)),
        )
    
    def create_config_card(self, name: str, data: Dict) -> ft.Container:
        """Create desktop configuration card"""
        delay = data.get("delay", 9999)
        status = data.get("status", "unknown")
        timestamp = data.get("timestamp", "")
        
        category = self.get_delay_category(delay, status)
        border_color = getattr(ft.Colors, category["color"])
        status_color = border_color
        quality = category["quality_text"]
        
        # تعیین آیکون بر اساس وضعیت و کیفیت
        if status != "online":
            status_icon = ft.Icons.SIGNAL_CELLULAR_OFF
        else:
            if delay < 100:
                status_icon = ft.Icons.SIGNAL_CELLULAR_ALT
            elif delay < 300:
                status_icon = ft.Icons.SIGNAL_CELLULAR_ALT_2_BAR
            elif delay < 500:
                status_icon = ft.Icons.SIGNAL_CELLULAR_ALT_1_BAR
            else:
                status_icon = ft.Icons.SIGNAL_CELLULAR_0_BAR

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = "N/A"

        card = ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Icon(status_icon, size=28, color=status_color),
                    ft.Column([
                        ft.Text(
                            name[:30] + "..." if len(name) > 30 else name,
                            size=16,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.WHITE,
                            tooltip=name,
                        ),
                        ft.Text(
                            quality,
                            size=12,
                            color=status_color,
                        ),
                    ], expand=True, spacing=2),
                ], alignment=ft.MainAxisAlignment.START, spacing=15),
                
                ft.Divider(height=20, color=ft.Colors.GREY_800),
                
                # Stats
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SPEED, size=16, color=ft.Colors.GREY_400),
                        ft.Text("Delay:", size=14, color=ft.Colors.GREY_400),
                        ft.Text(
                            f"{delay:.0f}ms" if delay < ADVANCED["offline_delay_threshold"] else "N/A",
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                    
                    ft.Row([
                        ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.Colors.GREY_400),
                        ft.Text("Last Test:", size=14, color=ft.Colors.GREY_400),
                        ft.Text(time_str, size=14, color=ft.Colors.WHITE),
                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                ], spacing=10),
                
                # Progress bar
                ft.Container(
                    content=ft.ProgressBar(
                        value=max(0, min(1, 1 - (delay / 1000))) if delay < 9999 else 0,
                        color=status_color,
                        bgcolor=ft.Colors.GREY_800,
                        height=6,
                    ),
                    margin=ft.margin.only(top=10),
                ),
            ], spacing=10),
            padding=ft.padding.all(20),
            border_radius=15,
            bgcolor=ft.Colors.GREY_800,
            border=ft.border.all(2, border_color),
            animate=ft.Animation(duration=300, curve=ft.AnimationCurve.EASE_IN_OUT),
            on_hover=self.on_card_hover,
        )
        
        return card
    
    def on_card_hover(self, e):
        """Handle card hover effect (desktop only)"""
        if not self.is_mobile:
            if e.data == "true":
                e.control.elevation = 10
                e.control.scale = 1.02
            else:
                e.control.elevation = 0
                e.control.scale = 1.0
            self.page.update()
    
    def load_results(self):
        """Load and display results from file"""
        try:
            if not self.results_file.exists():
                self.show_no_data()
                return
            
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get("results", {})
            
            if not results:
                self.show_no_data()
                return
            
            # Update statistics
            self.update_statistics(results)
            
            # Clear and rebuild config cards
            if self.is_mobile:
                self.configs_container.controls.clear()
            else:
                self.configs_grid.controls.clear()
            self.config_cards.clear()
            
            # Sort results
            sorted_results = self.sort_results(results, self.sort_dropdown.value)
            
            # Create cards based on view type
            for name, config_data in sorted_results:
                if self.is_mobile:
                    card = self.create_mobile_config_card(name, config_data)
                    self.config_cards[name] = card
                    self.configs_container.controls.append(card)
                else:
                    card = self.create_config_card(name, config_data)
                    self.config_cards[name] = card
                    self.configs_grid.controls.append(card)
            
            self.page.update()
            
        except Exception as e:
            print(f"Error loading results: {e}")
            self.show_error(str(e))
    
    def sort_results(self, results: Dict, sort_by: str) -> List:
        """Sort results based on selected criteria"""
        items = list(results.items())
        
        if sort_by == "name":
            items.sort(key=lambda x: x[0])
        elif sort_by == "delay":
            items.sort(key=lambda x: x[1].get("delay", 9999))
        elif sort_by == "delay_desc":
            items.sort(key=lambda x: x[1].get("delay", 9999), reverse=True)
        elif sort_by == "status":
            items.sort(key=lambda x: (x[1].get("status", "unknown"), x[1].get("delay", 9999)))
        
        return items
    
    def update_statistics(self, results: Dict):
        """Update statistics cards"""
        total = len(results)
        online = sum(1 for r in results.values() if r.get("status") == "online")
        offline = total - online
        
        delays = [r.get("delay", 0) for r in results.values() if r.get("status") == "online" and r.get("delay", 9999) < 9999]
        avg_delay = sum(delays) / len(delays) if delays else 0
        
        # Update stat cards based on view type
        if self.is_mobile:
            self.stats_row.controls[0].content.controls[1].value = str(total)
            self.stats_row.controls[1].content.controls[1].value = str(online)
            self.stats_row.controls[2].content.controls[1].value = str(offline)
            self.stats_row.controls[3].content.controls[1].value = f"{avg_delay:.0f}ms"
        else:
            self.stats_row.controls[0].content.controls[1].value = str(total)
            self.stats_row.controls[1].content.controls[1].value = str(online)
            self.stats_row.controls[2].content.controls[1].value = str(offline)
            self.stats_row.controls[3].content.controls[1].value = f"{avg_delay:.0f}ms"
    
    def filter_configs(self, e):
        """Filter configurations based on search text"""
        search_text = e.control.value.lower()
        
        for name, card in self.config_cards.items():
            if search_text in name.lower():
                card.visible = True
            else:
                card.visible = False
        
        self.page.update()
    
    def sort_configs(self, e):
        """Sort configurations based on selected criteria"""
        self.load_results()
    
    def toggle_theme(self, e):
        """Toggle between light and dark theme"""
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            e.control.icon = ft.Icons.DARK_MODE
            
            # Update theme colors for light mode from config
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=getattr(ft.Colors, LIGHT_THEME["primary"]),
                    primary_container=getattr(ft.Colors, LIGHT_THEME["primary_container"]),
                    secondary=getattr(ft.Colors, LIGHT_THEME["secondary"]),
                    background=getattr(ft.Colors, LIGHT_THEME["background"]),
                    surface=getattr(ft.Colors, LIGHT_THEME["surface"]),
                    on_primary=getattr(ft.Colors, LIGHT_THEME["on_primary"]),
                    on_secondary=getattr(ft.Colors, LIGHT_THEME["on_secondary"]),
                    on_background=getattr(ft.Colors, LIGHT_THEME["on_background"]),
                    on_surface=getattr(ft.Colors, LIGHT_THEME["on_surface"]),
                )
            )
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            e.control.icon = ft.Icons.LIGHT_MODE
            
            # Reset to dark theme from config
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=getattr(ft.Colors, DARK_THEME["primary"]),
                    primary_container=getattr(ft.Colors, DARK_THEME["primary_container"]),
                    secondary=getattr(ft.Colors, DARK_THEME["secondary"]),
                    background=getattr(ft.Colors, DARK_THEME["background"]),
                    surface=getattr(ft.Colors, DARK_THEME["surface"]),
                    on_primary=getattr(ft.Colors, DARK_THEME["on_primary"]),
                    on_secondary=getattr(ft.Colors, DARK_THEME["on_secondary"]),
                    on_background=getattr(ft.Colors, DARK_THEME["on_background"]),
                    on_surface=getattr(ft.Colors, DARK_THEME["on_surface"]),
                )
            )
        
        self.page.update()
        self.page.controls.clear()
        self.create_ui()
        self.load_results()
    
    def show_no_data(self):
        """Show no data message"""
        no_data_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INBOX, size=48 if self.is_mobile else 64, color=ft.Colors.GREY_600),
                ft.Text(
                    "No Data Available",
                    size=20 if self.is_mobile else 24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_600,
                ),
                ft.Text(
                    "Waiting for test results...",
                    size=14 if self.is_mobile else 16,
                    color=ft.Colors.GREY_500,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(30 if self.is_mobile else 50),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        if self.is_mobile:
            self.configs_container.controls.clear()
            self.configs_container.controls.append(no_data_container)
        else:
            self.configs_grid.controls.clear()
            self.configs_grid.controls.append(no_data_container)
        
        self.page.update()
    
    def show_error(self, error_msg: str):
        """Show error message"""
        error_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=48 if self.is_mobile else 64, color=ft.Colors.RED_400),
                ft.Text(
                    "Error Loading Data",
                    size=20 if self.is_mobile else 24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_400,
                ),
                ft.Text(
                    error_msg,
                    size=14 if self.is_mobile else 16,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(30 if self.is_mobile else 50),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        if self.is_mobile:
            self.configs_container.controls.clear()
            self.configs_container.controls.append(error_container)
        else:
            self.configs_grid.controls.clear()
            self.configs_grid.controls.append(error_container)
        
        self.page.update()
    
    def start_auto_refresh(self):
        """Start automatic refresh timer"""
        def refresh_loop():
            while True:
                time.sleep(AUTO_REFRESH_INTERVAL)  # Use config value
                try:
                    self.load_results()
                except Exception as e:
                    print(f"Auto-refresh error: {e}")
        
        self.update_timer = threading.Thread(target=refresh_loop, daemon=True)
        self.update_timer.start()
    
    def cleanup(self):
        """Cleanup resources"""
        # Timer will be cleaned up automatically as it's a daemon thread
        pass


def run_web_server(host: str = None, port: int = None):
    """Run the Flet web server with configurable host and port"""
    
    # Use config values if not provided
    if host is None:
        host = WEB_SERVER.get("host", "127.0.0.1")
    if port is None:
        port = WEB_SERVER.get("port", 8080)
    
    def main(page: ft.Page):
        # Create responsive dashboard
        dashboard = MonitorDashboard(page)
        
        # Handle cleanup on close
        def on_close(e):
            dashboard.cleanup()
        
        page.on_window_close = on_close
    
    # Run as web app
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        assets_dir="./assets" ,
        port=port,
        host=host,
    )


if __name__ == "__main__":
    # For testing, run as desktop app
    def main(page: ft.Page):
        dashboard = MonitorDashboard(page)
    
    ft.app(target=main)