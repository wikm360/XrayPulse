#!/usr/bin/env python3
"""
Web Interface for Xray Config Monitor
Modern and beautiful dashboard using Flet
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

class MonitorDashboard:
    """Modern monitoring dashboard using Flet"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.results_file = Path("./ping_results.json")
        self.config_cards = {}
        self.update_timer = None
        self.setup_page()
        self.create_ui()
        
    def setup_page(self):
        """Configure page settings"""
        self.page.title = "Xray Config Monitor"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.window.min_width = 1200
        self.page.window.min_height = 700
        
        # Modern color scheme
        self.page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=ft.Colors.BLUE_400,
                primary_container=ft.Colors.BLUE_900,
                secondary=ft.Colors.CYAN_400,
                background=ft.Colors.GREY_900,
                surface=ft.Colors.GREY_800,
                on_primary=ft.Colors.WHITE,
                on_secondary=ft.Colors.WHITE,
                on_background=ft.Colors.WHITE,
                on_surface=ft.Colors.WHITE,
            )
        )
    
    def create_ui(self):
        """Create the main user interface"""
        
        # Header with gradient background
        self.header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.MONITOR_HEART, size=40, color=ft.Colors.CYAN_400),
                    ft.Column([
                        ft.Text(
                            "Xray Config Monitor",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE
                        ),
                        ft.Text(
                            "Real-time Configuration Performance Monitoring",
                            size=14,
                            color=ft.Colors.GREY_400
                        ),
                    ], spacing=0),
                ], spacing=20),
                ft.Row([
                    self.create_status_indicator(),
                    # ft.IconButton(
                    #     icon=ft.Icons.REFRESH,
                    #     icon_size=24,
                    #     on_click=self.manual_refresh,
                    #     tooltip="Refresh Now",
                    #     icon_color=ft.Colors.WHITE,
                    # ),
                    ft.IconButton(
                        icon=ft.Icons.DARK_MODE if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.LIGHT_MODE,
                        icon_size=24,
                        on_click=self.toggle_theme,
                        tooltip="Toggle Theme",
                        icon_color=ft.Colors.WHITE,
                    ),
                ], spacing=10),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.Colors.BLUE_900, ft.Colors.PURPLE_900],
            ),
        )
        
        # Statistics cards
        self.stats_row = ft.Row(
            [
                self.create_stat_card("Total Configs", "0", ft.Icons.DNS, ft.Colors.BLUE_400),
                self.create_stat_card("Online", "0", ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN_400),
                self.create_stat_card("Offline", "0", ft.Icons.ERROR, ft.Colors.RED_400),
                self.create_stat_card("Avg Delay", "0ms", ft.Icons.SPEED, ft.Colors.ORANGE_400),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            spacing=20,
        )
        
        # Search and filter bar
        self.search_field = ft.TextField(
            label="Search configurations...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            filled=True,
            fill_color=ft.Colors.GREY_800,
            expand=True,
            on_change=self.filter_configs,
        )
        
        self.sort_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("name", "Name"),
                ft.dropdown.Option("delay", "Delay (Low to High)"),
                ft.dropdown.Option("delay_desc", "Delay (High to Low)"),
                ft.dropdown.Option("status", "Status"),
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
        
        # Config cards container
        self.configs_grid = ft.GridView(
            expand=True,
            runs_count=4,
            max_extent=350,
            child_aspect_ratio=1.2,
            spacing=20,
            run_spacing=20,
            padding=ft.padding.all(30),
        )
        
        # Main layout
        self.main_content = ft.Column([
            self.header,
            ft.Container(
                content=self.stats_row,
                padding=ft.padding.all(30),
            ),
            self.filter_bar,
            self.configs_grid,
        ], spacing=0, expand=True)
        
        # Add to page
        self.page.add(self.main_content)
        
        # Start auto-refresh
        self.start_auto_refresh()
        
        # Initial load
        self.load_results()
    
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
        """Create a statistics card"""
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
        """Create a configuration card"""
        delay = data.get("delay", 9999)
        status = data.get("status", "unknown")
        timestamp = data.get("timestamp", "")
        
        # Determine card appearance based on status
        if status == "online":
            if delay < 100:
                border_color = ft.Colors.GREEN_400
                status_icon = ft.Icons.SIGNAL_CELLULAR_ALT
                status_color = ft.Colors.GREEN_400
                quality = "Excellent"
            elif delay < 300:
                border_color = ft.Colors.BLUE_400
                status_icon = ft.Icons.SIGNAL_CELLULAR_ALT_2_BAR
                status_color = ft.Colors.BLUE_400
                quality = "Good"
            elif delay < 500:
                border_color = ft.Colors.ORANGE_400
                status_icon = ft.Icons.SIGNAL_CELLULAR_ALT_1_BAR
                status_color = ft.Colors.ORANGE_400
                quality = "Fair"
            else:
                border_color = ft.Colors.YELLOW_700
                status_icon = ft.Icons.SIGNAL_CELLULAR_0_BAR
                status_color = ft.Colors.YELLOW_700
                quality = "Poor"
        else:
            border_color = ft.Colors.RED_400
            status_icon = ft.Icons.SIGNAL_CELLULAR_OFF
            status_color = ft.Colors.RED_400
            quality = "Offline"
        
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
                            f"{delay:.0f}ms" if delay < 9999 else "N/A",
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
        """Handle card hover effect"""
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
            self.configs_grid.controls.clear()
            self.config_cards.clear()
            
            # Sort results
            sorted_results = self.sort_results(results, self.sort_dropdown.value)
            
            # Create cards
            for name, config_data in sorted_results:
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
        
        # Update stat cards
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
    
    def manual_refresh(self, e):
        """Manual refresh button handler"""
        self.load_results()
        
        # Show refresh animation
        e.control.rotate = ft.Rotate(2 * 3.14159, alignment=ft.alignment.center)
        self.page.update()
        time.sleep(0.5)
        e.control.rotate = ft.Rotate(0, alignment=ft.alignment.center)
        self.page.update()
    
    def toggle_theme(self, e):
        """Toggle between light and dark theme"""
        if self.page.theme_mode == ft.ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            e.control.icon = ft.Icons.DARK_MODE
            
            # Update theme colors for light mode
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=ft.Colors.BLUE_600,
                    primary_container=ft.Colors.BLUE_100,
                    secondary=ft.Colors.CYAN_600,
                    background=ft.Colors.GREY_100,
                    surface=ft.Colors.WHITE,
                    on_primary=ft.Colors.WHITE,
                    on_secondary=ft.Colors.WHITE,
                    on_background=ft.Colors.BLACK,
                    on_surface=ft.Colors.BLACK,
                )
            )
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            e.control.icon = ft.Icons.LIGHT_MODE
            
            # Reset to dark theme
            self.page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary=ft.Colors.BLUE_400,
                    primary_container=ft.Colors.BLUE_900,
                    secondary=ft.Colors.CYAN_400,
                    background=ft.Colors.GREY_900,
                    surface=ft.Colors.GREY_800,
                    on_primary=ft.Colors.WHITE,
                    on_secondary=ft.Colors.WHITE,
                    on_background=ft.Colors.WHITE,
                    on_surface=ft.Colors.WHITE,
                )
            )
        
        self.page.update()
        self.load_results()  # Reload to apply theme changes
    
    def show_no_data(self):
        """Show no data message"""
        self.configs_grid.controls.clear()
        self.configs_grid.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.INBOX, size=64, color=ft.Colors.GREY_600),
                    ft.Text(
                        "No Data Available",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        "Waiting for test results...",
                        size=16,
                        color=ft.Colors.GREY_500,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(50),
                alignment=ft.alignment.center,
                expand=True,
            )
        )
        self.page.update()
    
    def show_error(self, error_msg: str):
        """Show error message"""
        self.configs_grid.controls.clear()
        self.configs_grid.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color=ft.Colors.RED_400),
                    ft.Text(
                        "Error Loading Data",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_400,
                    ),
                    ft.Text(
                        error_msg,
                        size=16,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(50),
                alignment=ft.alignment.center,
                expand=True,
            )
        )
        self.page.update()
    
    def start_auto_refresh(self):
        """Start automatic refresh timer"""
        def refresh_loop():
            while True:
                time.sleep(10)  # Refresh every 10 seconds
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


class AdvancedDashboard(MonitorDashboard):
    """Extended dashboard with additional features"""
    
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.add_advanced_features()
    
    def add_advanced_features(self):
        """Add advanced monitoring features"""
        
        # Add chart view toggle
        self.view_toggle = ft.SegmentedButton(
            selected={"grid"},
            segments=[
                ft.Segment(
                    value="grid",
                    label=ft.Text("Grid View"),
                    icon=ft.Icon(ft.Icons.GRID_VIEW),
                ),
                ft.Segment(
                    value="chart",
                    label=ft.Text("Chart View"),
                    icon=ft.Icon(ft.Icons.SHOW_CHART),
                ),
                ft.Segment(
                    value="table",
                    label=ft.Text("Table View"),
                    icon=ft.Icon(ft.Icons.TABLE_CHART),
                ),
            ],
            on_change=self.change_view,
        )
        
        # Add to filter bar
        self.filter_bar.content.controls.append(self.view_toggle)
        
        # Create chart view
        self.chart_view = self.create_chart_view()
        
        # Create table view
        self.table_view = self.create_table_view()
    
    def create_chart_view(self) -> ft.Container:
        """Create chart visualization"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Performance Chart",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Container(
                    content=ft.Text("Chart visualization coming soon..."),
                    height=400,
                    bgcolor=ft.Colors.GREY_800,
                    border_radius=10,
                    alignment=ft.alignment.center,
                ),
            ]),
            padding=ft.padding.all(30),
            visible=False,
        )
    
    def create_table_view(self) -> ft.Container:
        """Create table view"""
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Delay (ms)", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Quality", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Last Test", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.GREY_800),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_800),
            column_spacing=50,
            heading_row_color=ft.Colors.GREY_800,
            data_row_color={
                ft.ControlState.HOVERED: ft.Colors.GREY_800,
                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
            },
        )
        
        return ft.Container(
            content=ft.Column([
                self.data_table,
            ], scroll=ft.ScrollMode.AUTO),
            padding=ft.padding.all(30),
            visible=False,
            expand=True,
        )
    
    def change_view(self, e):
        """Change between different view modes"""
        selected_view = list(e.control.selected)[0]
        
        # Hide all views
        self.configs_grid.visible = False
        self.chart_view.visible = False
        self.table_view.visible = False
        
        # Show selected view
        if selected_view == "grid":
            self.configs_grid.visible = True
        elif selected_view == "chart":
            self.chart_view.visible = True
        elif selected_view == "table":
            self.table_view.visible = True
            self.update_table_data()
        
        self.page.update()
    
    def update_table_data(self):
        """Update table with current data"""
        try:
            if not self.results_file.exists():
                return
            
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            results = data.get("results", {})
            
            # Clear existing rows
            self.data_table.rows.clear()
            
            # Add new rows
            for name, config_data in results.items():
                delay = config_data.get("delay", 9999)
                status = config_data.get("status", "unknown")
                timestamp = config_data.get("timestamp", "")
                
                # Determine quality
                if status == "online":
                    if delay < 100:
                        quality = "Excellent"
                        status_color = ft.Colors.GREEN_400
                    elif delay < 300:
                        quality = "Good"
                        status_color = ft.Colors.BLUE_400
                    elif delay < 500:
                        quality = "Fair"
                        status_color = ft.Colors.ORANGE_400
                    else:
                        quality = "Poor"
                        status_color = ft.Colors.YELLOW_700
                else:
                    quality = "N/A"
                    status_color = ft.Colors.RED_400
                
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = "N/A"
                
                self.data_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(name[:40] + "..." if len(name) > 40 else name)),
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(status.upper(), color=ft.Colors.WHITE, size=12),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=5,
                                )
                            ),
                            ft.DataCell(ft.Text(f"{delay:.0f}" if delay < 9999 else "N/A")),
                            ft.DataCell(ft.Text(quality, color=status_color)),
                            ft.DataCell(ft.Text(time_str)),
                        ]
                    )
                )
            
        except Exception as e:
            print(f"Error updating table: {e}")


def run_web_server(host: str = "127.0.0.1", port: int = 7070):
    """Run the Flet web server"""
    
    def main(page: ft.Page):
        # Use advanced dashboard
        dashboard = AdvancedDashboard(page)
        
        # Handle cleanup on close
        def on_close(e):
            dashboard.cleanup()
        
        page.on_window_close = on_close
    
    # Run as web app
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
        host=host,
    )


if __name__ == "__main__":
    # For testing, run as desktop app
    def main(page: ft.Page):
        dashboard = AdvancedDashboard(page)
    
    ft.app(target=main)