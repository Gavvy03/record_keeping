"""
Streamlit application for Swing Trading Chart Observation Journal - Phase 1
"""

import streamlit as st
import sys
import os
from datetime import datetime, date

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import services as app_services
from domain import services as ds
import pandas as pd


def init_session_state():
    """Initialize session state variables with clean defaults."""
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Dashboard"
    if "selected_stock_id" not in st.session_state:
        st.session_state.selected_stock_id = None
    if "selected_obs_id" not in st.session_state:
        st.session_state.selected_obs_id = None
    if "last_created_stock_id" not in st.session_state:
        st.session_state.last_created_stock_id = None


def render_dashboard():
    """Render dashboard view with KPI metrics, status chart, and recent observations."""
    st.title("📊 Dashboard")
    st.caption("Swing Trading Chart Observation Journal")
    
    data = app_services.get_dashboard_data()
    status_map = data.get("status_map", {})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Stocks", data["total_stocks"])
    col2.metric("Total Observations", data["total_observations"])
    col3.metric("Watching", status_map.get("Watching", 0))
    col4.metric("Triggered", status_map.get("Triggered", 0))
    
    col_chart, col_recent = st.columns([1, 2])
    
    with col_chart:
        st.subheader("Observations by Status")
        status_items = [(c["status"], c["count"]) for c in data["counts_by_status"]]
        if status_items:
            status_df = pd.DataFrame(status_items, columns=["Status", "Count"])
            st.bar_chart(status_df.set_index("Status"))
        else:
            st.info("No observations recorded yet.")
            
    with col_recent:
        st.subheader("Recent Observations")
        recent = data["recent_observations"]
        if recent:
            recent_rows = []
            for obs in recent:
                recent_rows.append({
                    "Date": obs.observation_date,
                    "Stock": obs.stock_ticker or "N/A",
                    "Company": obs.stock_name or "N/A",
                    "Timeframe": obs.timeframe,
                    "Setup": obs.setup_type,
                    "Status": obs.status,
                    "Trade Plan": obs.get_trade_plan_summary(),
                })
            st.dataframe(pd.DataFrame(recent_rows), hide_index=True, use_container_width=True)
        else:
            st.info("No observations yet. Click 'Add Observation' in the sidebar.")


def render_add_stock_section():
    """Render collapsible Add New Stock form."""
    with st.expander("➕ Register New Stock (Optional)", expanded=False):
        with st.form("form_add_new_stock", clear_on_submit=True):
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                ticker = st.text_input("Ticker Symbol *", placeholder="e.g. HBLENG, AAPL", key="stock_reg_ticker")
                company_name = st.text_input("Company Name *", placeholder="e.g. HBL Engine Limited", key="stock_reg_name")
            with col_s2:
                exchange = st.text_input("Exchange *", value="PSX", key="stock_reg_exchange")
                sector = st.text_input("Sector", placeholder="e.g. Automotive, Tech", key="stock_reg_sector")
            
            submit_stock = st.form_submit_button("Save Stock", key="btn_submit_stock")
            if submit_stock:
                new_stock, err = app_services.create_new_stock_form(
                    ticker=ticker,
                    company_name=company_name,
                    exchange=exchange,
                    sector=sector
                )
                if err:
                    st.error(err)
                else:
                    st.success(f"Stock '{new_stock.ticker}' registered successfully!")
                    st.session_state.last_created_stock_id = new_stock.id
                    st.session_state.selected_stock_id = new_stock.id
                    st.rerun()


def render_add_observation():
    """Render revised Observation Form matching the Phase 1 specification."""
    st.title("➕ Add Observation")
    st.caption("Record a manual chart observation with Trade Plan and Chart Levels")
    
    render_add_stock_section()
    
    stocks = ds.get_stocks()
    if not stocks:
        st.warning("No stocks registered in database. Please register a stock above first.")
        return
    
    # Pre-select newly registered stock if available
    default_stock_idx = 0
    if st.session_state.last_created_stock_id:
        for idx, s in enumerate(stocks):
            if s.id == st.session_state.last_created_stock_id:
                default_stock_idx = idx
                break
    elif st.session_state.selected_stock_id:
        for idx, s in enumerate(stocks):
            if s.id == st.session_state.selected_stock_id:
                default_stock_idx = idx
                break
                
    with st.form("form_add_observation", clear_on_submit=False):
        # 1. Observation Context
        st.subheader("1. General Information")
        col_ctx1, col_ctx2 = st.columns(2)
        with col_ctx1:
            stock_sel = st.selectbox(
                "Stock *",
                options=stocks,
                index=default_stock_idx,
                format_func=lambda x: f"{x.ticker} — {x.company_name} ({x.exchange})",
                key="add_obs_stock_select"
            )
        with col_ctx2:
            obs_date = st.date_input("Observation Date *", value=date.today(), key="add_obs_date")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            timeframe = st.selectbox("Timeframe *", ds.get_all_timeframes(), index=1, key="add_obs_timeframe")
        with col_m2:
            setup_type = st.selectbox("Setup Type *", ds.get_all_setup_types(), key="add_obs_setup")
        with col_m3:
            pattern = st.text_input("Pattern", placeholder="e.g. Double Bottom, Channel", key="add_obs_pattern")
        with col_m4:
            market_structure = st.text_input("Market Structure", placeholder="e.g. Bullish, Sideways", key="add_obs_market_structure")
        
        status = st.selectbox("Initial Status *", ds.get_all_statuses(), index=0, key="add_obs_status")
        
        # 2. Trade Plan (Single Price or Range)
        st.subheader("2. Trade Plan")
        st.caption("Each field can be a single price or a price range (enter Min and Max).")
        col_tp1, col_tp2, col_tp3 = st.columns(3)
        
        with col_tp1:
            st.markdown("**Entry**")
            entry_from = st.number_input("Entry (Price or Min)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_entry_from")
            entry_to = st.number_input("Entry Max (if range)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_entry_to")
            
        with col_tp2:
            st.markdown("**Stop Loss**")
            sl_from = st.number_input("Stop Loss (Price or Min)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_sl_from")
            sl_to = st.number_input("Stop Loss Max (if range)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_sl_to")
            
        with col_tp3:
            st.markdown("**Target**")
            tgt_from = st.number_input("Target (Price or Min)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_tgt_from")
            tgt_to = st.number_input("Target Max (if range)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_tgt_to")
        
        # 3. Chart Levels (Exactly 3 Support slots & 3 Resistance slots)
        st.subheader("3. Chart Levels")
        st.caption("Manually entered Support and Resistance levels (single price or range). Leave 0.00 for empty slots.")
        
        col_sup, col_res = st.columns(2)
        with col_sup:
            st.markdown("#### Supports")
            st.markdown("**Support 1**")
            c_s1_a, c_s1_b = st.columns(2)
            s1_from = c_s1_a.number_input("Price / Min", min_value=0.0, step=0.5, format="%.2f", key="add_obs_s1_from")
            s1_to = c_s1_b.number_input("Max (Range)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_s1_to")
            
            st.markdown("**Support 2**")
            c_s2_a, c_s2_b = st.columns(2)
            s2_from = c_s2_a.number_input("Price / Min ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_s2_from")
            s2_to = c_s2_b.number_input("Max (Range) ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_s2_to")
            
            st.markdown("**Support 3**")
            c_s3_a, c_s3_b = st.columns(2)
            s3_from = c_s3_a.number_input("Price / Min  ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_s3_from")
            s3_to = c_s3_b.number_input("Max (Range)  ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_s3_to")
            
        with col_res:
            st.markdown("#### Resistances")
            st.markdown("**Resistance 1**")
            c_r1_a, c_r1_b = st.columns(2)
            r1_from = c_r1_a.number_input("Price / Min", min_value=0.0, step=0.5, format="%.2f", key="add_obs_r1_from")
            r1_to = c_r1_b.number_input("Max (Range)", min_value=0.0, step=0.5, format="%.2f", key="add_obs_r1_to")
            
            st.markdown("**Resistance 2**")
            c_r2_a, c_r2_b = st.columns(2)
            r2_from = c_r2_a.number_input("Price / Min ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_r2_from")
            r2_to = c_r2_b.number_input("Max (Range) ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_r2_to")
            
            st.markdown("**Resistance 3**")
            c_r3_a, c_r3_b = st.columns(2)
            r3_from = c_r3_a.number_input("Price / Min  ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_r3_from")
            r3_to = c_r3_b.number_input("Max (Range)  ", min_value=0.0, step=0.5, format="%.2f", key="add_obs_r3_to")

        # 4. Analysis
        st.subheader("4. Analysis")
        key_obs = st.text_area("Key Observation", placeholder="Main technical takeaway or trigger conditions...", key="add_obs_key_obs")
        notes = st.text_area("Notes", placeholder="Additional context, volume observations, market environment...", key="add_obs_notes")
        
        submit_obs = st.form_submit_button("💾 Save Observation", use_container_width=True, key="btn_submit_observation")
        if submit_obs:
            trade_plan = {
                "entry_price_from": entry_from if entry_from > 0 else None,
                "entry_price_to": entry_to if entry_to > 0 else None,
                "stop_loss_from": sl_from if sl_from > 0 else None,
                "stop_loss_to": sl_to if sl_to > 0 else None,
                "target_price_from": tgt_from if tgt_from > 0 else None,
                "target_price_to": tgt_to if tgt_to > 0 else None,
            }
            
            levels = []
            slot_data = [
                ("Support", "Support 1", s1_from, s1_to),
                ("Support", "Support 2", s2_from, s2_to),
                ("Support", "Support 3", s3_from, s3_to),
                ("Resistance", "Resistance 1", r1_from, r1_to),
                ("Resistance", "Resistance 2", r2_from, r2_to),
                ("Resistance", "Resistance 3", r3_from, r3_to),
            ]
            for l_type, l_lbl, p_from, p_to in slot_data:
                if p_from > 0:
                    levels.append({
                        "level_type": l_type,
                        "label": l_lbl,
                        "price_from": p_from,
                        "price_to": p_to if p_to > 0 else None,
                        "priority": "High" if "1" in l_lbl else "Medium",
                        "notes": None
                    })
            
            new_obs, error = app_services.create_new_observation_form(
                stock_id=stock_sel.id,
                observation_date=str(obs_date),
                timeframe=timeframe,
                market_structure=market_structure,
                setup_type=setup_type,
                pattern=pattern,
                status=status,
                key_observation=key_obs,
                notes=notes,
                trade_plan=trade_plan,
                levels=levels
            )
            if error:
                st.error(error)
            else:
                st.success(f"Observation recorded successfully for {stock_sel.ticker}!")
                st.session_state.selected_stock_id = stock_sel.id
                st.session_state.selected_obs_id = new_obs.id


def render_search_history():
    """Render Search / History functionality with rich multi-parameter filters."""
    st.title("🔍 Search / History")
    st.caption("Search and filter all historical observations with compact, clickable results")
    
    stocks = ds.get_stocks()
    stock_options = [None] + stocks
    
    with st.expander("Filter Controls", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            stock_filter_sel = st.selectbox(
                "Filter by Stock",
                options=stock_options,
                format_func=lambda x: "All Stocks" if x is None else f"{x.ticker} — {x.company_name}",
                key="search_stock_filter"
            )
        with col_f2:
            setup_filter = st.selectbox("Setup Type", ["All"] + ds.get_all_setup_types(), key="search_setup_filter")
        with col_f3:
            status_filter = st.selectbox("Status", ["All"] + ds.get_all_statuses(), key="search_status_filter")
        
        col_f4, col_f5, col_f6 = st.columns(3)
        with col_f4:
            pattern_filter = st.text_input("Pattern", placeholder="Filter by pattern name...", key="search_pattern_filter")
        with col_f5:
            market_filter = st.text_input("Market Structure", placeholder="e.g. Bullish", key="search_market_filter")
        with col_f6:
            c_d1, c_d2 = st.columns(2)
            date_from = c_d1.date_input("Date From", value=None, key="search_date_from")
            date_to = c_d2.date_input("Date To", value=None, key="search_date_to")
            
        search_query = st.text_input("Free-text Search (Key Observation & Notes)", placeholder="Search keywords across analysis...", key="search_text_filter")
        
    stock_id_param = stock_filter_sel.id if stock_filter_sel else None
    
    results = app_services.get_watchlist_data(
        stock_filter=stock_id_param,
        setup_filter=setup_filter,
        pattern_filter=pattern_filter,
        status_filter=status_filter,
        market_structure_filter=market_filter,
        date_from=str(date_from) if date_from else None,
        date_to=str(date_to) if date_to else None,
        search_text=search_query
    )
    
    st.markdown(f"**Found {len(results)} matching observation(s)**")
    
    if results:
        table_rows = []
        for obs in results:
            key_preview = (obs.key_observation[:60] + "...") if obs.key_observation and len(obs.key_observation) > 60 else (obs.key_observation or "-")
            table_rows.append({
                "ID": obs.id,
                "Date": obs.observation_date,
                "Stock": obs.stock_ticker or "N/A",
                "Company": obs.stock_name or "N/A",
                "Timeframe": obs.timeframe,
                "Setup": obs.setup_type,
                "Pattern": obs.pattern or "-",
                "Status": obs.status,
                "Trade Plan": obs.get_trade_plan_summary(),
                "Key Observation": key_preview
            })
        st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)
        
        # Clickable selector to view observation
        st.markdown("#### Open Observation Details")
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            selected_id = st.selectbox(
                "Select observation to inspect or edit:",
                options=[obs.id for obs in results],
                format_func=lambda x: f"ID #{x} — {next((o.stock_ticker for o in results if o.id == x), '')} on {next((o.observation_date for o in results if o.id == x), '')} ({next((o.setup_type for o in results if o.id == x), '')})",
                key="search_result_select"
            )
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Inspect Observation", key="btn_inspect_obs"):
                st.session_state.selected_obs_id = selected_id
                target_obs = next((o for o in results if o.id == selected_id), None)
                if target_obs:
                    st.session_state.selected_stock_id = target_obs.stock_id
                st.session_state.nav_page = "Stock History / Observation Detail"
                st.rerun()
    else:
        st.info("No observations found matching the specified search criteria.")


def render_watchlist():
    """Render Watchlist view with proper stock join and CSV export."""
    st.title("📋 Watchlist")
    st.caption("Active swing trading setups and observations")
    
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter Status", ["All"] + ds.get_all_statuses(), index=1, key="wl_status_filter")
    with col2:
        setup_filter = st.selectbox("Filter Setup", ["All"] + ds.get_all_setup_types(), key="wl_setup_filter")
        
    observations = app_services.get_watchlist_data(
        status_filter=status_filter,
        setup_filter=setup_filter
    )
    
    if observations:
        table_rows = []
        for obs in observations:
            table_rows.append({
                "Date": obs.observation_date,
                "Stock": obs.stock_ticker or "N/A",
                "Company": obs.stock_name or "N/A",
                "Timeframe": obs.timeframe,
                "Setup": obs.setup_type,
                "Pattern": obs.pattern or "-",
                "Status": obs.status,
                "Trade Plan": obs.get_trade_plan_summary(),
                "Key Observation": obs.key_observation or "-"
            })
        st.dataframe(pd.DataFrame(table_rows), hide_index=True, use_container_width=True)
        
        col_exp, col_jump = st.columns([1, 2])
        with col_exp:
            if st.button("⬇️ Export to CSV", key="btn_export_csv"):
                file_path = app_services.export_observations_to_csv(observations)
                st.success(f"Exported {len(observations)} observations to '{file_path}'")
                
        with col_jump:
            jump_id = st.selectbox(
                "Open stock history for:",
                options=list({o.stock_id: f"{o.stock_ticker} — {o.stock_name}" for o in observations}.items()),
                format_func=lambda x: x[1],
                key="wl_jump_stock"
            )
            if st.button("View Stock History", key="btn_jump_stock"):
                st.session_state.selected_stock_id = jump_id[0]
                st.session_state.nav_page = "Stock History / Observation Detail"
                st.rerun()
    else:
        st.info("No observations found for the selected filters.")


def render_stock_history_and_detail():
    """Render Stock History showing chronological observations newest first, plus Observation Detail & Edit."""
    st.title("📈 Stock History & Observation Detail")
    st.caption("Chronological observations for a stock (newest first) and complete observation editor")
    
    stocks = ds.get_stocks()
    if not stocks:
        st.warning("No stocks available in database. Add a stock in 'Add Observation'.")
        return
        
    # Select stock
    selected_stock_idx = 0
    if st.session_state.selected_stock_id:
        for idx, s in enumerate(stocks):
            if s.id == st.session_state.selected_stock_id:
                selected_stock_idx = idx
                break
                
    selected_stock = st.selectbox(
        "Select Stock:",
        options=stocks,
        index=selected_stock_idx,
        format_func=lambda x: f"{x.ticker} — {x.company_name} ({x.exchange})",
        key="stock_hist_stock_selector"
    )
    st.session_state.selected_stock_id = selected_stock.id
    
    # Stock Summary Card
    observations = ds.get_stock_history(selected_stock.id)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ticker", selected_stock.ticker)
    c2.metric("Company", selected_stock.company_name)
    c3.metric("Exchange", selected_stock.exchange)
    c4.metric("Total Observations", len(observations))
    
    st.markdown("---")
    st.subheader(f"Chronological History for {selected_stock.ticker} ({len(observations)} records, newest first)")
    
    if not observations:
        st.info(f"No observations recorded yet for {selected_stock.ticker}.")
        return
        
    for obs in observations:
        is_highlighted = (st.session_state.selected_obs_id == obs.id)
        expander_title = f"{obs.observation_date} [{obs.timeframe}] — {obs.setup_type} ({obs.status})"
        if obs.pattern:
            expander_title += f" • {obs.pattern}"
        if is_highlighted:
            expander_title = f"👉 {expander_title} (Selected)"
            
        with st.expander(expander_title, expanded=is_highlighted):
            tab_view, tab_edit, tab_history = st.tabs(["👁️ View Details", "✏️ Edit Observation", "🕒 Status History"])
            
            with tab_view:
                # Trade Plan View
                st.markdown("##### Trade Plan")
                col_tp_v1, col_tp_v2, col_tp_v3 = st.columns(3)
                col_tp_v1.markdown(f"**Entry:** {obs.get_price_range_str(obs.entry_price_from, obs.entry_price_to)}")
                col_tp_v2.markdown(f"**Stop Loss:** {obs.get_price_range_str(obs.stop_loss_from, obs.stop_loss_to)}")
                col_tp_v3.markdown(f"**Target:** {obs.get_price_range_str(obs.target_price_from, obs.target_price_to)}")
                
                # Chart Levels View
                st.markdown("##### Chart Levels")
                lvl_dict = obs.get_levels_dict()
                col_lvl_s, col_lvl_r = st.columns(2)
                with col_lvl_s:
                    st.markdown("**Supports:**")
                    for s_num in [1, 2, 3]:
                        s_key = f"Support {s_num}"
                        lvl = lvl_dict[s_key]
                        val = obs.get_price_range_str(lvl.price_from, lvl.price_to) if lvl else "-"
                        st.write(f"- {s_key}: **{val}**")
                with col_lvl_r:
                    st.markdown("**Resistances:**")
                    for r_num in [1, 2, 3]:
                        r_key = f"Resistance {r_num}"
                        lvl = lvl_dict[r_key]
                        val = obs.get_price_range_str(lvl.price_from, lvl.price_to) if lvl else "-"
                        st.write(f"- {r_key}: **{val}**")
                        
                # Analysis
                st.markdown("##### Analysis")
                st.markdown(f"**Market Structure:** {obs.market_structure or '-'}")
                st.markdown(f"**Key Observation:** {obs.key_observation or '-'}")
                if obs.notes:
                    st.markdown(f"**Notes:** {obs.notes}")
                    
            with tab_edit:
                st.markdown("##### Complete Observation Editor")
                with st.form(f"form_edit_obs_{obs.id}"):
                    c_e1, c_e2, c_e3 = st.columns(3)
                    with c_e1:
                        e_date = st.date_input("Date", value=datetime.strptime(obs.observation_date, "%Y-%m-%d").date() if obs.observation_date else date.today(), key=f"e_date_{obs.id}")
                    with c_e2:
                        tf_idx = ds.get_all_timeframes().index(obs.timeframe) if obs.timeframe in ds.get_all_timeframes() else 0
                        e_timeframe = st.selectbox("Timeframe", ds.get_all_timeframes(), index=tf_idx, key=f"e_tf_{obs.id}")
                    with c_e3:
                        st_idx = ds.get_all_setup_types().index(obs.setup_type) if obs.setup_type in ds.get_all_setup_types() else 0
                        e_setup = st.selectbox("Setup Type", ds.get_all_setup_types(), index=st_idx, key=f"e_setup_{obs.id}")
                        
                    c_e4, c_e5, c_e6 = st.columns(3)
                    with c_e4:
                        status_idx = ds.get_all_statuses().index(obs.status) if obs.status in ds.get_all_statuses() else 0
                        e_status = st.selectbox("Status", ds.get_all_statuses(), index=status_idx, key=f"e_status_{obs.id}")
                    with c_e5:
                        e_pattern = st.text_input("Pattern", value=obs.pattern or "", key=f"e_pattern_{obs.id}")
                    with c_e6:
                        e_market = st.text_input("Market Structure", value=obs.market_structure or "", key=f"e_market_{obs.id}")
                        
                    st.markdown("**Trade Plan (Single Price or Range)**")
                    col_ep1, col_ep2, col_ep3 = st.columns(3)
                    with col_ep1:
                        e_efrom = st.number_input("Entry (Price / Min)", value=float(obs.entry_price_from or 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_efrom_{obs.id}")
                        e_eto = st.number_input("Entry Max (Range)", value=float(obs.entry_price_to or 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_eto_{obs.id}")
                    with col_ep2:
                        e_slfrom = st.number_input("SL (Price / Min)", value=float(obs.stop_loss_from or 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_slfrom_{obs.id}")
                        e_slto = st.number_input("SL Max (Range)", value=float(obs.stop_loss_to or 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_slto_{obs.id}")
                    with col_ep3:
                        e_tgtfrom = st.number_input("Target (Price / Min)", value=float(obs.target_price_from or 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_tgtfrom_{obs.id}")
                        e_tgtto = st.number_input("Target Max (Range)", value=float(obs.target_price_to or 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_tgtto_{obs.id}")
                        
                    st.markdown("**Chart Levels (Support 1..3 and Resistance 1..3)**")
                    curr_lvl = obs.get_levels_dict()
                    col_es, col_er = st.columns(2)
                    with col_es:
                        st.markdown("**Supports**")
                        s1 = curr_lvl["Support 1"]
                        cs1_a, cs1_b = st.columns(2)
                        es1_from = cs1_a.number_input("Support 1 Min", value=float(s1.price_from if s1 else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_s1f_{obs.id}")
                        es1_to = cs1_b.number_input("Support 1 Max", value=float(s1.price_to if s1 and s1.price_to else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_s1t_{obs.id}")
                        
                        s2 = curr_lvl["Support 2"]
                        cs2_a, cs2_b = st.columns(2)
                        es2_from = cs2_a.number_input("Support 2 Min", value=float(s2.price_from if s2 else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_s2f_{obs.id}")
                        es2_to = cs2_b.number_input("Support 2 Max", value=float(s2.price_to if s2 and s2.price_to else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_s2t_{obs.id}")
                        
                        s3 = curr_lvl["Support 3"]
                        cs3_a, cs3_b = st.columns(2)
                        es3_from = cs3_a.number_input("Support 3 Min", value=float(s3.price_from if s3 else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_s3f_{obs.id}")
                        es3_to = cs3_b.number_input("Support 3 Max", value=float(s3.price_to if s3 and s3.price_to else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_s3t_{obs.id}")

                    with col_er:
                        st.markdown("**Resistances**")
                        r1 = curr_lvl["Resistance 1"]
                        cr1_a, cr1_b = st.columns(2)
                        er1_from = cr1_a.number_input("Resistance 1 Min", value=float(r1.price_from if r1 else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_r1f_{obs.id}")
                        er1_to = cr1_b.number_input("Resistance 1 Max", value=float(r1.price_to if r1 and r1.price_to else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_r1t_{obs.id}")
                        
                        r2 = curr_lvl["Resistance 2"]
                        cr2_a, cr2_b = st.columns(2)
                        er2_from = cr2_a.number_input("Resistance 2 Min", value=float(r2.price_from if r2 else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_r2f_{obs.id}")
                        er2_to = cr2_b.number_input("Resistance 2 Max", value=float(r2.price_to if r2 and r2.price_to else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_r2t_{obs.id}")
                        
                        r3 = curr_lvl["Resistance 3"]
                        cr3_a, cr3_b = st.columns(2)
                        er3_from = cr3_a.number_input("Resistance 3 Min", value=float(r3.price_from if r3 else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_r3f_{obs.id}")
                        er3_to = cr3_b.number_input("Resistance 3 Max", value=float(r3.price_to if r3 and r3.price_to else 0.0), min_value=0.0, step=0.5, format="%.2f", key=f"e_r3t_{obs.id}")

                    e_key_obs = st.text_area("Key Observation", value=obs.key_observation or "", key=f"e_kobs_{obs.id}")
                    e_notes = st.text_area("Notes", value=obs.notes or "", key=f"e_notes_{obs.id}")
                    status_note = st.text_input("Status Change Note (if updating status)", placeholder="e.g. Pattern confirmed by breakout candle...", key=f"e_snote_{obs.id}")
                    
                    btn_save_changes = st.form_submit_button("Save Changes", key=f"btn_save_edit_{obs.id}")
                    if btn_save_changes:
                        edit_tp = {
                            "entry_price_from": e_efrom if e_efrom > 0 else None,
                            "entry_price_to": e_eto if e_eto > 0 else None,
                            "stop_loss_from": e_slfrom if e_slfrom > 0 else None,
                            "stop_loss_to": e_slto if e_slto > 0 else None,
                            "target_price_from": e_tgtfrom if e_tgtfrom > 0 else None,
                            "target_price_to": e_tgtto if e_tgtto > 0 else None,
                        }
                        edit_levels = []
                        slots = [
                            ("Support", "Support 1", es1_from, es1_to),
                            ("Support", "Support 2", es2_from, es2_to),
                            ("Support", "Support 3", es3_from, es3_to),
                            ("Resistance", "Resistance 1", er1_from, er1_to),
                            ("Resistance", "Resistance 2", er2_from, er2_to),
                            ("Resistance", "Resistance 3", er3_from, er3_to),
                        ]
                        for l_type, l_lbl, p_from, p_to in slots:
                            if p_from > 0:
                                edit_levels.append({
                                    "level_type": l_type,
                                    "label": l_lbl,
                                    "price_from": p_from,
                                    "price_to": p_to if p_to > 0 else None,
                                    "priority": "High" if "1" in l_lbl else "Medium",
                                    "notes": None
                                })
                        
                        ok, msg = app_services.update_observation_form(
                            observation_id=obs.id,
                            observation_date=str(e_date),
                            timeframe=e_timeframe,
                            market_structure=e_market,
                            setup_type=e_setup,
                            pattern=e_pattern,
                            status=e_status,
                            key_observation=e_key_obs,
                            notes=e_notes,
                            trade_plan=edit_tp,
                            levels=edit_levels,
                            status_notes=status_note if status_note else "Status updated"
                        )
                        if ok:
                            st.success("Observation updated successfully!")
                            st.rerun()
                        else:
                            st.error(msg)
                            
            with tab_history:
                st.markdown("##### Status Transition Audit Trail")
                # Fetch fresh status history
                history_records = ds.get_observation_status_history(obs.id)
                if history_records:
                    hist_data = []
                    for h in history_records:
                        hist_data.append({
                            "Changed At": h["changed_at"],
                            "Status": h["status"],
                            "Notes": h["notes"] or "-"
                        })
                    st.dataframe(pd.DataFrame(hist_data), hide_index=True, use_container_width=True)
                else:
                    st.info("No status history recorded.")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Swing Trading Journal",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    pages = {
        "Dashboard": render_dashboard,
        "Add Observation": render_add_observation,
        "Search / History": render_search_history,
        "Watchlist": render_watchlist,
        "Stock History / Observation Detail": render_stock_history_and_detail,
    }
    
    # Navigation
    current_page_idx = list(pages.keys()).index(st.session_state.nav_page) if st.session_state.nav_page in pages else 0
    selected_page = st.sidebar.radio(
        "Navigation",
        options=list(pages.keys()),
        index=current_page_idx,
        key="main_navigation_radio"
    )
    
    if selected_page != st.session_state.nav_page:
        st.session_state.nav_page = selected_page
        st.rerun()
        
    pages[st.session_state.nav_page]()


if __name__ == "__main__":
    main()

