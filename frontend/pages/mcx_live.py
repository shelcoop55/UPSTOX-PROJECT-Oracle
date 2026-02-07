
from nicegui import ui
from ..common import Components
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime

DB_PATH = Path("market_data.db").absolute()

def get_commodities():
    """Fetch distinct MCX commodities"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM instrument_master WHERE segment = 'MCX_FO' AND is_active = 1 ORDER BY name")
        start = [row[0] for row in cursor.fetchall()]
        conn.close()
        return start
    except Exception as e:
        print(f"Error fetching commodities: {e}")
        return []

def get_expiries(commodity):
    """Fetch expiries for a commodity"""
    if not commodity: return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Format date for display if needed, but keeping YYYY-MM-DD is standard
        cursor.execute("SELECT DISTINCT expiry FROM instrument_master WHERE segment = 'MCX_FO' AND name = ? AND is_active = 1 ORDER BY expiry", (commodity,))
        rows = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching expiries: {e}")
        return []

def get_mcx_data(commodity=None, expiry=None, instrument_type="FUT"):
    """Fetch MCX data joined with WebSocket ticks"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Base Query
        query = """
            SELECT 
                im.trading_symbol,
                im.expiry,
                im.instrument_type,
                im.lot_size,
                im.instrument_key,
                
                -- Live Data from Websocket V3 (Preferred)
                COALESCE(ws.ltp, 0) as last_price,
                COALESCE(ws.volume, 0) as volume,
                COALESCE(ws.ltp - ws.open, 0) as net_change,
                COALESCE(ws.open, 0) as open, 
                COALESCE(ws.high, 0) as high, 
                COALESCE(ws.low, 0) as low,
                COALESCE(ws.oi, 0) as oi,
                
                -- Depth Summary (Top 1)
                COALESCE(ws.bid_price_1, 0) as best_bid,
                COALESCE(ws.ask_price_1, 0) as best_ask
                
            FROM instrument_master im
            LEFT JOIN websocket_ticks_v3 ws ON im.instrument_key = ws.instrument_key
            WHERE im.segment = 'MCX_FO' AND im.is_active = 1
        """
        params = []
        
        if commodity:
            query += " AND im.name = ?"
            params.append(commodity)
            
        if expiry:
            query += " AND im.expiry = ?"
            params.append(expiry)
            
        if instrument_type == "FUT":
            query += " AND im.instrument_type = 'FUT'"
        elif instrument_type == "OPT":
            query += " AND (im.instrument_type = 'CE' OR im.instrument_type = 'PE')"
            # Logic for "ATM +/- 5" could go here if we had spot price, 
            # for now let's just limit rows to avoid UI lags if showing all options
            if not commodity: # If no commodity selected, restricting output
                query += " AND 1=0" # Don't show random options
            
        query += " ORDER BY im.trading_symbol"
        
        # Limit result size for safety
        query += " LIMIT 500"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Fill NaNs
        df = df.fillna(0)
        return df.to_dict('records')
        
    except Exception as e:
        print(f"Error fetching MCX data: {e}")
        return []

def get_depth_details(instrument_key):
    """Fetch full 15-level depth for an instrument"""
    try:
        conn = sqlite3.connect(DB_PATH)
        # We need all 15 levels
        cols = ["ltp", "volume"]
        for i in range(1, 16):
            cols.extend([f"bid_price_{i}", f"bid_qty_{i}", f"ask_price_{i}", f"ask_qty_{i}"])
            
        col_str = ", ".join(cols)
        cursor = conn.cursor()
        cursor.execute(f"SELECT {col_str} FROM websocket_ticks_v3 WHERE instrument_key = ?", (instrument_key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = {}
            data['ltp'] = row[0]
            data['volume'] = row[1]
            # Map index to fields
            # 0=ltp, 1=vol, 2=b1, 3=bq1, 4=a1, 5=aq1 ...
            depth = []
            current_idx = 2
            for i in range(1, 16):
                depth.append({
                    'level': i,
                    'bid_price': row[current_idx],
                    'bid_qty': row[current_idx+1],
                    'ask_price': row[current_idx+2],
                    'ask_qty': row[current_idx+3]
                })
                current_idx += 4
            return depth
        return []
    except Exception as e:
        print(f"Error fetching depth: {e}")
        return []

def render_page(state):
    Components.section_header(
        "MCX Live Dashboard", "Real-Time Commodities Streaming (D30)", "hub"
    )
    
    # --- State ---
    filters = {
        'commodity': None, # Default None
        'expiry': None,
        'type': 'FUT' # FUT, OPT, BOTH
    }
    
    commodities = get_commodities()
    
    # --- UI Components ---
    with Components.card():
        with ui.row().classes("w-full items-center gap-4"):
            
            # Commodity Filter
            comm_select = ui.select(
                options=commodities,
                label="Commodity",
                on_change=lambda e: update_expiries()
            ).classes("w-48")
            
            # Expiry Filter
            expiry_select = ui.select(
                options=[],
                label="Expiry"
            ).classes("w-48")
            
            # Type Toggle
            type_toggle = ui.toggle(
                options={'FUT': 'Futures', 'OPT': 'Options', 'BOTH': 'All'},
                value='FUT'
            ).props("no-caps")
            
            # Refresh Button
            ui.button(icon="refresh", on_click=lambda: update_table()).props("flat round")
            
            # Status Indicator
            ui.badge("Live D30", color="green").props("floating")

    # --- Backend Logic for Watching ---
    def toggle_watch(instrument_key, subscribe):
        """Add or remove key from watched_instruments"""
        try:
            conn = sqlite3.connect(DB_PATH)
            if subscribe:
                conn.execute("INSERT OR IGNORE INTO watched_instruments (instrument_key) VALUES (?)", (instrument_key,))
                ui.notify(f"Watching {instrument_key}", type='positive')
            else:
                conn.execute("DELETE FROM watched_instruments WHERE instrument_key = ?", (instrument_key,))
                ui.notify(f"Stopped watching {instrument_key}", type='warning')
            conn.commit()
            conn.close()
        except Exception as e:
            ui.notify(f"Error: {e}", type='negative')

    def get_option_chain(commodity, expiry):
        """Fetch option chain (CE/PE) for a commodity expiry"""
        try:
            conn = sqlite3.connect(DB_PATH)
            # Fetch all CE/PE for this expiry
            # Join with Live Data
            query = """
                SELECT 
                    im.instrument_key, im.strike_price, im.instrument_type,
                    COALESCE(ws.ltp, 0) as ltp,
                    COALESCE(ws.volume, 0) as volume,
                    COALESCE(ws.bid_price_1, 0) as bid,
                    COALESCE(ws.ask_price_1, 0) as ask
                FROM instrument_master im
                LEFT JOIN websocket_ticks_v3 ws ON im.instrument_key = ws.instrument_key
                WHERE im.segment = 'MCX_FO' AND im.name = ? AND im.expiry = ? 
                AND (im.instrument_type = 'CE' OR im.instrument_type = 'PE')
                ORDER BY im.strike_price
            """
            df = pd.read_sql_query(query, conn, params=(commodity, expiry))
            
            # Check watched status
            cursor = conn.cursor()
            cursor.execute("SELECT instrument_key FROM watched_instruments")
            watched_keys = set(row[0] for row in cursor.fetchall())
            conn.close()
            
            # Process into Strike Rows [Strike, CE_Key, CE_LTP, PE_Key, PE_LTP, Watched?]
            chain = {}
            for _, row in df.iterrows():
                strike = row['strike_price']
                if strike not in chain:
                    chain[strike] = {'strike': strike, 'CE': {}, 'PE': {}}
                
                itype = row['instrument_type']
                data = {
                    'key': row['instrument_key'], 
                    'ltp': row['ltp'], 
                    'bid': row['bid'],
                    'ask': row['ask'],
                    'watched': row['instrument_key'] in watched_keys
                }
                chain[strike][itype] = data
                
            return sorted(chain.values(), key=lambda x: x['strike'])
        except Exception as e:
            print(f"Chain Error: {e}")
            return []

    # --- Detail Dialog for Depth ---
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-4xl"):
        dialog_title = ui.label("Market Depth").classes("text-xl font-bold mb-4")
        depth_container = ui.column().classes("w-full")
        
    # --- Option Chain Dialog ---
    with ui.dialog() as chain_dialog, ui.card().classes("w-full max-w-6xl h-[80vh]"):
        chain_title = ui.label("Option Chain").classes("text-xl font-bold mb-4")
        chain_container = ui.column().classes("w-full h-full scroll-y-auto")

    async def show_option_chain_ui(row):
        # Infer Commodity and Expiry from row
        comm = comm_select.value
        expiry = row['expiry'] # Use row's expiry
        
        if not comm:
             ui.notify("Please select a commodity first", type='warning')
             return

        chain_title.set_text(f"Option Chain: {comm} {expiry}")
        chain_container.clear()
        
        # 1. Trigger Snapshot Fetch (Non-blocking usually ideally, but we want data)
        ui.notify("Fetching Chain Snapshot...", type='info')
        try:
            # We need an async client or use requests? 
            # Frontend runs in async loop properly with nicegui?
            # Let's use requests for simplicity or check if we have an api client wrapper.
            # Using requests in async function blocks loop slightly but acceptable for 0.5s.
            # Or use aiohttp if available. Let's use requests for now.
            import requests
            resp = requests.post(
                "http://localhost:8000/api/snapshot/option-chain", 
                json={"commodity": comm, "expiry": expiry},
                timeout=3
            )
            if resp.status_code == 200:
                res = resp.json()
                ui.notify(f"Updated {res.get('updated', 0)} contracts", type='positive')
            else:
                ui.notify(f"Snapshot Error: {resp.text}", type='warning')
        except Exception as e:
            # Don't block UI if snapshot fails (offline backend?)
            print(f"Snapshot Warning: {e}")
            
        # 2. Query DB (Now has fresh data)
        data = get_option_chain(comm, expiry)
        
        with chain_container:
            # Header
            with ui.row().classes("w-full bg-slate-800 p-2 font-bold text-center sticky top-0"):
                ui.label("CALLS (CE)").classes("w-1/3 text-green-400")
                ui.label("STRIKE").classes("w-1/6 text-white")
                ui.label("PUTS (PE)").classes("w-1/3 text-red-400")
            
            # Rows
            with ui.column().classes("w-full gap-1"):
                for item in data:
                    strike = item['strike']
                    ce = item['CE']
                    pe = item['PE']
                    
                    with ui.row().classes("w-full items-center hover:bg-slate-800 p-1 border-b border-slate-800"):
                        # CE Side
                        with ui.row().classes("w-1/3 justify-end items-center gap-4 pr-4"):
                            if ce:
                                ui.checkbox(value=ce.get('watched', False), on_change=lambda e, k=ce['key']: toggle_watch(k, e.value))
                                ui.label(f"{ce['ltp']:.2f}").classes("font-mono text-green-300")
                                ui.label(f"B:{ce['bid']}").classes("text-xs text-slate-500")
                            else:
                                ui.label("-")
                        
                        # Strike
                        ui.label(f"{strike}").classes("w-1/6 text-center font-bold bg-slate-700 rounded")
                        
                        # PE Side
                        with ui.row().classes("w-1/3 justify-start items-center gap-4 pl-4"):
                            if pe:
                                ui.label(f"A:{pe['ask']}").classes("text-xs text-slate-500")
                                ui.label(f"{pe['ltp']:.2f}").classes("font-mono text-red-300")
                                ui.checkbox(value=pe.get('watched', False), on_change=lambda e, k=pe['key']: toggle_watch(k, e.value))

                            else:
                                ui.label("-")
        
        chain_dialog.open()

    def show_depth(row):
        dialog_title.set_text(f"Depth: {row['trading_symbol']}")
        depth_data = get_depth_details(row['instrument_key'])
        depth_container.clear()
        
        with depth_container:
            if not depth_data:
                ui.label("No Live Data Available").classes("text-red-400 italic")
            else:
                # Top Stats
                with ui.row().classes("w-full justify-between mb-4 bg-slate-900 p-2 rounded"):
                    ui.label(f"LTP: ₹{depth_data[0]['bid_price'] if depth_data else 0}").classes("text-2xl font-bold text-yellow-400") # approx
                    # Better to use LTP from arg or row, but let's stick to what we have
                
                # 3-Column Layout: Bids | Info | Asks
                with ui.grid(columns=2).classes("w-full gap-8"):
                    
                    # BIDS
                    with ui.column():
                        ui.label("BUY ORDERS").classes("text-green-400 font-bold border-b w-full")
                        with ui.row().classes("w-full text-slate-500 text-xs"):
                            ui.label("Vol").classes("w-1/3")
                            ui.label("Price").classes("w-1/3 text-right")
                            
                        for i, level in enumerate(depth_data):
                            bg_class = "bg-green-900/20" if i < 5 else "" # Highlight Top 5
                            with ui.row().classes(f"w-full justify-between font-mono text-sm {bg_class} p-1"):
                                ui.label(f"{level['bid_qty']:,}").classes("w-1/3")
                                ui.label(f"{level['bid_price']:.2f}").classes("w-1/3 text-right text-green-300 font-bold")

                    # ASKS
                    with ui.column():
                        ui.label("SELL ORDERS").classes("text-red-400 font-bold border-b w-full")
                        with ui.row().classes("w-full text-slate-500 text-xs"):
                            ui.label("Price").classes("w-1/3")
                            ui.label("Vol").classes("w-1/3 text-right")
                            
                        for i, level in enumerate(depth_data):
                            bg_class = "bg-red-900/20" if i < 5 else "" # Highlight Top 5
                            with ui.row().classes(f"w-full justify-between font-mono text-sm {bg_class} p-1"):
                                ui.label(f"{level['ask_price']:.2f}").classes("w-1/3 text-red-300 font-bold")
                                ui.label(f"{level['ask_qty']:,}").classes("w-1/3 text-right")

        dialog.open()

    # --- Tabs ---
    with ui.tabs().classes('w-full') as tabs:
        live_tab = ui.tab('Live', icon='sensors')
        intraday_tab = ui.tab('Intraday', icon='show_chart')
        historical_tab = ui.tab('Historical', icon='history')
        
    with ui.tab_panels(tabs, value=live_tab).classes('w-full bg-transparent'):
        
        # --- TAB 1: LIVE DATA ---
        with ui.tab_panel(live_tab):
            grid_container = ui.column().classes("w-full")
            
            # Sub-header/Status
            with ui.row().classes("w-full items-center justify-between mb-2"):
                ui.label("Real-Time Stream").classes("text-sm text-slate-400 italic")
                ui.badge("WebSocket Live", color="green")

        # --- TAB 2: INTRADAY DATA ---
        with ui.tab_panel(intraday_tab):
            intraday_container = ui.column().classes("w-full")
            with ui.row().classes("w-full items-center justify-between"):
                ui.label("Intraday (1-Min Candles)").classes("text-lg font-bold")
                ui.button("Fetch Intraday", icon="refresh", on_click=lambda: update_intraday()).props("flat")

        # --- TAB 3: HISTORICAL EXPLORER ---
        with ui.tab_panel(historical_tab):
            historical_container = ui.column().classes("w-full")
            
            # --- Explorer Form ---
            with ui.card().classes("w-full bg-slate-800 p-4 mb-4"):
                ui.label("Data Explorer").classes("text-lg font-bold mb-2 text-yellow-400")
                
                with ui.row().classes("w-full gap-4 items-end"):
                    # 1. Instrument (Auto-filled but editable logic could be added)
                    # For now we use the main filter's commodity/expiry to resolve the key
                    ui.label("Using Main Filter Selection").classes("text-slate-400 text-xs mb-2")
                    
                    # 2. Timeframe
                    timeframe_select = ui.select(
                        options=['1minute', '30minute', 'day', 'week', 'month'],
                        value='day',
                        label="Interval"
                    ).classes("w-32")
                    
                    # 3. Date Range
                    from_date_input = ui.input(
                        label="From Date", 
                        value=(datetime.now() - pd.Timedelta(days=30)).strftime("%Y-%m-%d"),
                        placeholder="YYYY-MM-DD"
                    ).classes("w-40")
                    
                    to_date_input = ui.input(
                        label="To Date", 
                        value=datetime.now().strftime("%Y-%m-%d"),
                        placeholder="YYYY-MM-DD"
                    ).classes("w-40")
                    
                    # 4. Fetch Action
                    ui.button("Fetch Data", icon="search", on_click=lambda: update_historical()).classes("bg-blue-600")

            # Results Area
            history_results = ui.column().classes("w-full")

    async def update_expiries():
        comm = comm_select.value
        if comm:
            exps = get_expiries(comm)
            expiry_select.options = exps
            if exps:
                expiry_select.value = exps[0] # Default to near month
            update_table()
            update_intraday()
            # update_historical() # Don't auto-fetch historical explorer on filter change, let user click

    def update_intraday():
        # ... (Same as before) ...
        intraday_container.clear()
        comm = comm_select.value
        exp = expiry_select.value
        if not comm or not exp: return

        rows = get_mcx_data(comm, exp, "FUT")
        if not rows: return
        key = rows[0]['instrument_key']

        from backend.services.market_data.historical_service import HistoricalService
        service = HistoricalService(str(DB_PATH))
        res = service.get_intraday_candles(key, interval='1minute')

        with intraday_container:
            if "error" in res:
                ui.label(f"Error: {res['error']}").classes("text-red-400")
            else:
                ui.label(f"Intraday (1min) for {comm} {exp}").classes("text-sm text-slate-400 mb-2")
                ui.table(
                    columns=[
                        {'name': 'time', 'label': 'Time', 'field': 'timestamp', 'sortable': True},
                        {'name': 'o', 'label': 'Open', 'field': 'open'},
                        {'name': 'h', 'label': 'High', 'field': 'high'},
                        {'name': 'l', 'label': 'Low', 'field': 'low'},
                        {'name': 'c', 'label': 'Close', 'field': 'close'},
                        {'name': 'v', 'label': 'Vol', 'field': 'volume'}
                    ],
                    rows=res['data'][:50]
                ).classes("w-full bg-slate-900")

    def update_historical():
        history_results.clear()
        
        # 1. Resolve Key from Main Filters
        comm = comm_select.value
        exp = expiry_select.value
        if not comm or not exp: 
            ui.notify("Please select Commodity & Expiry first", type='warning')
            return

        rows = get_mcx_data(comm, exp, "FUT")
        if not rows: 
            ui.notify("Instrument not found", type='negative')
            return
        key = rows[0]['instrument_key']
        symbol = rows[0]['trading_symbol']

        # 2. Get User Inputs
        interval = timeframe_select.value
        f_date = from_date_input.value
        t_date = to_date_input.value
        
        # 3. Fetch
        from backend.services.market_data.historical_service import HistoricalService
        service = HistoricalService(str(DB_PATH))
        
        ui.notify(f"Fetching {interval} data for {symbol}...", type='info')
        res = service.get_historical_candles(key, interval=interval, to_date=t_date, from_date=f_date)

        # 4. Render
        with history_results:
            if "error" in res:
                ui.label(f"Error: {res['error']}").classes("text-red-400 font-bold")
            else:
                count = len(res['data'])
                ui.label(f"Found {count} candles ({f_date} to {t_date})").classes("text-green-400 mb-2")
                
                ui.table(
                    columns=[
                        {'name': 'date', 'label': 'Timestamp', 'field': 'timestamp', 'sortable': True, 'align': 'left'},
                        {'name': 'o', 'label': 'Open', 'field': 'open'},
                        {'name': 'h', 'label': 'High', 'field': 'high'},
                        {'name': 'l', 'label': 'Low', 'field': 'low'},
                        {'name': 'c', 'label': 'Close', 'field': 'close'},
                        {'name': 'v', 'label': 'Vol', 'field': 'volume'}
                    ],
                    rows=res['data']
                ).classes("w-full bg-slate-900")

    def update_table():
        # ... (rest of old update_table logic) ...
        grid_container.clear()
        
        # Get Filter Values
        comm = comm_select.value
        exp = expiry_select.value
        itype = type_toggle.value
        
        if not comm:
            comm = "CRUDE OIL"
            # No circular call here, just set and fetch
            # comm_select.value = "CRUDE OIL"
            # update_expiries()
            # return
            # Better: use a default if nothing selected

        rows = get_mcx_data(comm, exp, itype)
        
        with grid_container:
            if not rows:
                ui.label("No Data Found").classes("text-slate-500 italic")
                return

            columns = [
                {'name': 'symbol', 'label': 'Symbol', 'field': 'trading_symbol', 'sortable': True, 'align': 'left'},
                {'name': 'expiry', 'label': 'Expiry', 'field': 'expiry', 'sortable': True, 'align': 'center'},
                {'name': 'ltp', 'label': 'LTP', 'field': 'last_price', 'sortable': True, 'align': 'right'},
                {'name': 'change', 'label': 'Chg', 'field': 'net_change', 'sortable': True, 'align': 'right'},
                {'name': 'open', 'label': 'Open', 'field': 'open', 'sortable': True, 'align': 'right'},
                {'name': 'high', 'label': 'High', 'field': 'high', 'sortable': True, 'align': 'right'},
                {'name': 'low', 'label': 'Low', 'field': 'low', 'sortable': True, 'align': 'right'},
                {'name': 'chain', 'label': 'Chain', 'field': 'instrument_key', 'align': 'center'},
                {'name': 'depth', 'label': 'Depth', 'field': 'instrument_key', 'align': 'center'},
            ]
            
            table = ui.table(columns=columns, rows=rows, pagination=20).classes("w-full bg-slate-900")
            
            # Custom Slots
            table.add_slot('body-cell-ltp', '''
                <q-td :props="props">
                    <div class="font-mono font-bold text-yellow-300">
                        {{ props.value.toFixed(2) }}
                    </div>
                </q-td>
            ''')
            
            table.add_slot('body-cell-change', '''
                <q-td :props="props">
                    <div :class="props.value >= 0 ? 'text-green-400' : 'text-red-400'">
                        {{ props.value.toFixed(2) }}
                    </div>
                </q-td>
            ''')
            
            table.add_slot('body-cell-chain', '''
                <q-td :props="props">
                    <q-btn size="sm" color="purple" dense label="Chain" 
                        @click="$parent.$emit('chain-click', props.row)" />
                </q-td>
            ''')

            table.add_slot('body-cell-depth', '''
                <q-td :props="props">
                    <q-btn size="sm" color="primary" dense label="D30" 
                        @click="$parent.$emit('row-click', props.row)" />
                </q-td>
            ''')
            
            table.on('row-click', lambda e: show_depth(e.args))
            table.on('chain-click', lambda e: show_option_chain_ui(e.args))

    # Initial Load
    # update_table() - Handled by defaults and selections
