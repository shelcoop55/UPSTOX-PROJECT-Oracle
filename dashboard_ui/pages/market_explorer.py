"""
Market Explorer Page - Real-time Market Data with Database Integration
Displays Broad Market Indices, Derivatives, and Sectoral Indices with filtering
"""

from nicegui import ui, run
from ..common import Components
from datetime import datetime
import sqlite3
import asyncio
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "market_data.db"
API_BASE = "http://localhost:8000"


# ============================================================================
# 📊 DATABASE QUERIES
# ============================================================================

def get_broad_market_indices() -> List[Dict]:
    """Get all broad market indices from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                index_code,
                index_name,
                index_subcategory,
                constituent_count
            FROM index_master
            WHERE index_category = 'broad'
            ORDER BY 
                CASE 
                    WHEN index_code = 'NIFTY50' THEN 1
                    WHEN index_code = 'NIFTY100' THEN 2
                    WHEN index_code = 'NIFTY200' THEN 3
                    WHEN index_code = 'NIFTY500' THEN 4
                    ELSE 5
                END,
                index_name
        """)
        
        indices = []
        for row in cursor.fetchall():
            indices.append({
                'code': row[0],
                'name': row[1],
                'category': row[2] or 'broad',
                'expected_count': row[3] or 0
            })
        
        conn.close()
        return indices
        
    except Exception as e:
        print(f"Error fetching broad indices: {e}")
        return []


def get_sectoral_indices() -> List[Dict]:
    """Get all sectoral indices from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                index_code,
                index_name,
                index_subcategory,
                constituent_count
            FROM index_master
            WHERE index_category = 'sectoral'
            ORDER BY index_name
        """)
        
        indices = []
        for row in cursor.fetchall():
            indices.append({
                'code': row[0],
                'name': row[1],
                'sector': row[2] or 'sectoral',
                'expected_count': row[3] or 0
            })
        
        conn.close()
        return indices
        
    except Exception as e:
        print(f"Error fetching sectoral indices: {e}")
        return []


def get_index_constituents(index_code: str) -> List[Dict]:
    """Get constituents of a specific index"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ic.symbol,
                ic.company_name,
                ic.isin,
                ic.series,
                ss.sector_name,
                ss.industry
            FROM index_constituents ic
            LEFT JOIN stock_sectors st ON ic.symbol = st.symbol
            LEFT JOIN sectors ss ON st.sector_id = ss.id
            WHERE ic.index_code = ? AND ic.is_active = 1
            ORDER BY ic.symbol
        """, (index_code,))
        
        constituents = []
        for row in cursor.fetchall():
            constituents.append({
                'symbol': row[0],
                'company_name': row[1] or row[0],
                'isin': row[2],
                'series': row[3],
                'sector': row[4] or 'N/A',
                'industry': row[5] or 'N/A'
            })
        
        conn.close()
        return constituents
        
    except Exception as e:
        print(f"Error fetching constituents for {index_code}: {e}")
        return []


def get_index_stats(index_code: str) -> Dict:
    """Get statistics for an index"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get actual constituent count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM index_constituents 
            WHERE index_code = ? AND is_active = 1
        """, (index_code,))
        actual_count = cursor.fetchone()[0]
        
        # Get sector distribution
        cursor.execute("""
            SELECT s.sector_name, COUNT(*) as count
            FROM index_constituents ic
            JOIN stock_sectors st ON ic.symbol = st.symbol
            JOIN sectors s ON st.sector_id = s.id
            WHERE ic.index_code = ? AND ic.is_active = 1
            GROUP BY s.sector_name
            ORDER BY count DESC
            LIMIT 5
        """, (index_code,))
        
        top_sectors = []
        for row in cursor.fetchall():
            top_sectors.append({'sector': row[0], 'count': row[1]})
        
        conn.close()
        
        return {
            'actual_count': actual_count,
            'top_sectors': top_sectors
        }
        
    except Exception as e:
        print(f"Error fetching stats for {index_code}: {e}")
        return {'actual_count': 0, 'top_sectors': []}


# ============================================================================
# 📊 UI RENDERING
# ============================================================================

def render_page(state):
    """Main page render function"""
    Components.section_header(
        "Market Explorer",
        "Explore NSE Indices and Constituents",
        "insights",
    )
    
    # Check if database is populated
    broad_indices = get_broad_market_indices()
    sectoral_indices = get_sectoral_indices()
    
    if not broad_indices and not sectoral_indices:
        with Components.card():
            ui.label("⚠️ Market data not loaded").classes("text-xl text-yellow-500 mb-2")
            ui.label("Please run the database setup script:").classes("text-slate-400")
            ui.code("python scripts/setup_market_database.py").classes("mt-2")
        return
    
    # Tab navigation
    with ui.tabs().classes("w-full") as tabs:
        broad_tab = ui.tab("Broad Market Indices", icon="insights")
        sectoral_tab = ui.tab("Sectoral Indices", icon="business")
        derivatives_tab = ui.tab("Derivatives", icon="trending_up")
    
    # Tab panels
    with ui.tab_panels(tabs, value=broad_tab).classes("w-full mt-4"):
        # Broad Market Indices Tab
        with ui.tab_panel(broad_tab):
            render_broad_market_tab(broad_indices)
        
        # Sectoral Indices Tab
        with ui.tab_panel(sectoral_tab):
            render_sectoral_tab(sectoral_indices)
        
        # Derivatives Tab
        with ui.tab_panel(derivatives_tab):
            with Components.card():
                ui.label("🚧 Derivatives Explorer Coming Soon").classes("text-xl text-yellow-500")
                ui.label("This section will display F&O contracts and derivatives data.").classes("text-slate-400 mt-2")


def render_broad_market_tab(indices: List[Dict]):
    """Render Broad Market Indices tab with filters"""
    
    # State for selected index
    selected_index = {'code': None, 'name': None}
    
    with ui.row().classes("w-full gap-4"):
        # Left panel: Index selector
        with ui.column().classes("w-1/3"):
            with Components.card():
                ui.label("Select Index").classes("text-lg font-bold mb-4")
                
                # Filter buttons
                with ui.row().classes("w-full gap-2 mb-4"):
                    filter_all = ui.button("All", icon="list").props("outline dense").classes("flex-1")
                    filter_large = ui.button("Large Cap", icon="trending_up").props("outline dense").classes("flex-1")
                    filter_mid = ui.button("Mid Cap", icon="show_chart").props("outline dense").classes("flex-1")
                    filter_small = ui.button("Small Cap", icon="insights").props("outline dense").classes("flex-1")
                
                # Index list container
                index_list_container = ui.column().classes("w-full gap-2 max-h-[600px] overflow-y-auto")
                
                def render_index_list(filter_category: Optional[str] = None):
                    """Render filtered index list"""
                    index_list_container.clear()
                    
                    filtered_indices = indices
                    if filter_category:
                        filtered_indices = [idx for idx in indices if filter_category in idx['category']]
                    
                    with index_list_container:
                        for idx in filtered_indices:
                            with ui.card().classes("w-full p-3 cursor-pointer hover:bg-slate-700/50 transition-colors") as card:
                                with ui.row().classes("w-full justify-between items-center"):
                                    with ui.column().classes("gap-1"):
                                        ui.label(idx['name']).classes("font-semibold text-white")
                                        ui.label(f"{idx['expected_count']} stocks • {idx['category']}").classes("text-xs text-slate-400")
                                    ui.icon("chevron_right").classes("text-slate-400")
                                
                                # Click handler
                                card.on('click', lambda idx=idx: load_index_details(idx))
                
                # Filter button handlers
                filter_all.on('click', lambda: render_index_list(None))
                filter_large.on('click', lambda: render_index_list('largecap'))
                filter_mid.on('click', lambda: render_index_list('midcap'))
                filter_small.on('click', lambda: render_index_list('smallcap'))
                
                # Initial render
                render_index_list()
        
        # Right panel: Index details
        with ui.column().classes("w-2/3"):
            details_container = ui.column().classes("w-full gap-4")
            
            with details_container:
                # Placeholder
                with Components.card():
                    ui.label("👈 Select an index to view details").classes("text-lg text-slate-400 text-center py-12")
            
            def load_index_details(idx: Dict):
                """Load and display index details"""
                selected_index['code'] = idx['code']
                selected_index['name'] = idx['name']
                
                details_container.clear()
                
                with details_container:
                    # Header card
                    with Components.card():
                        with ui.row().classes("w-full justify-between items-start"):
                            with ui.column().classes("gap-2"):
                                ui.label(idx['name']).classes("text-2xl font-bold text-white")
                                ui.label(f"Index Code: {idx['code']}").classes("text-sm text-slate-400")
                            
                            ui.button("Refresh", icon="refresh", on_click=lambda: load_index_details(idx)).props("outline")
                    
                    # Stats card
                    stats = get_index_stats(idx['code'])
                    
                    with Components.card():
                        ui.label("Index Statistics").classes("text-lg font-bold mb-4")
                        
                        with ui.row().classes("w-full gap-4"):
                            with ui.column().classes("flex-1 bg-blue-500/10 p-4 rounded-lg"):
                                ui.label("Total Constituents").classes("text-xs text-slate-400 uppercase")
                                ui.label(str(stats['actual_count'])).classes("text-3xl font-bold text-blue-400")
                            
                            with ui.column().classes("flex-1 bg-purple-500/10 p-4 rounded-lg"):
                                ui.label("Expected").classes("text-xs text-slate-400 uppercase")
                                ui.label(str(idx['expected_count'])).classes("text-3xl font-bold text-purple-400")
                            
                            with ui.column().classes("flex-1 bg-green-500/10 p-4 rounded-lg"):
                                ui.label("Data Status").classes("text-xs text-slate-400 uppercase")
                                status = "✅ Complete" if stats['actual_count'] >= idx['expected_count'] * 0.9 else "⚠️ Partial"
                                ui.label(status).classes("text-xl font-bold text-green-400")
                        
                        # Top sectors
                        if stats['top_sectors']:
                            ui.label("Top 5 Sectors").classes("text-sm font-bold mt-4 mb-2")
                            for sector_data in stats['top_sectors']:
                                with ui.row().classes("w-full justify-between items-center py-1"):
                                    ui.label(sector_data['sector']).classes("text-slate-300")
                                    ui.label(f"{sector_data['count']} stocks").classes("text-slate-500 text-sm")
                    
                    # Constituents table
                    constituents = get_index_constituents(idx['code'])
                    
                    with Components.card():
                        ui.label(f"Constituents ({len(constituents)})").classes("text-lg font-bold mb-4")
                        
                        if constituents:
                            # Search box
                            search_input = ui.input(
                                label="Search stocks",
                                placeholder="Type symbol or company name..."
                            ).props("outlined dense clearable").classes("w-full mb-4")
                            
                            # Table columns
                            columns = [
                                {'name': 'symbol', 'label': 'Symbol', 'field': 'symbol', 'align': 'left', 'sortable': True},
                                {'name': 'company_name', 'label': 'Company Name', 'field': 'company_name', 'align': 'left', 'sortable': True},
                                {'name': 'sector', 'label': 'Sector', 'field': 'sector', 'align': 'left', 'sortable': True},
                                {'name': 'industry', 'label': 'Industry', 'field': 'industry', 'align': 'left', 'sortable': True},
                                {'name': 'series', 'label': 'Series', 'field': 'series', 'align': 'center', 'sortable': True},
                            ]
                            
                            table = ui.table(
                                columns=columns,
                                rows=constituents,
                                row_key='symbol',
                                pagination={'rowsPerPage': 20, 'sortBy': 'symbol', 'descending': False}
                            ).classes("w-full")
                            
                            # Search filter
                            def filter_table():
                                query = search_input.value.lower() if search_input.value else ""
                                if query:
                                    filtered = [
                                        c for c in constituents 
                                        if query in c['symbol'].lower() or query in c['company_name'].lower()
                                    ]
                                    table.rows = filtered
                                else:
                                    table.rows = constituents
                                table.update()
                            
                            search_input.on('input', lambda: filter_table())
                        else:
                            ui.label("No constituents data available").classes("text-slate-400 italic")


def render_sectoral_tab(indices: List[Dict]):
    """Render Sectoral Indices tab"""
    with Components.card():
        ui.label("Sectoral Indices").classes("text-xl font-bold mb-4")
        
        if not indices:
            ui.label("No sectoral indices data available").classes("text-slate-400 italic")
            return
        
        # Grid of sectoral indices
        with ui.grid(columns=3).classes("w-full gap-4"):
            for idx in indices:
                with ui.card().classes("p-4 cursor-pointer hover:bg-slate-700/50 transition-colors"):
                    ui.label(idx['name']).classes("font-semibold text-white mb-2")
                    ui.label(f"Sector: {idx['sector']}").classes("text-xs text-slate-400")
                    stats = get_index_stats(idx['code'])
                    ui.label(f"{stats['actual_count']} constituents").classes("text-sm text-blue-400 mt-2")
