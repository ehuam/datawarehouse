"""
This page was pulled out notebook to allow users to tune settings if finviz structure changed.
"""
# SITE INVENTORY - USER DECOMPOSITION
SITE_INVENTORY = {
    "control_plane": ["screener-combo-title", "screener-combo-select"],
    "navigation_tabs": ["Descriptiv", "ExchangeAn", "OverviewVa"],
    "data_rows": ["styled-row"],
    "layout_noise": [
        "header", "navbar", "footer", "modal-elite-ad", "script", "noscript", "iframe",
        "js-elite-features-root", "notifications-container", "notifications-react-root",
        "dialogs-react-root", "root", "IC_D_1x1_1", "portal/_r_5_", "ICUid_Iframe",
        "img", "svg", "use", "js-feature-discovery-root", "screener-presets-root"
    ],
    "pagination_drop": ["pageSelect"],
    "pagination_option": ["option"],
    "navigation_controls": ["screener_pagination", "pages-combo", "is-next", "screener-pages"],
}

FUNCTIONAL_AREAS = {
    "SCREENER_FILTERS": "filter-table-top",
    "DATA": "screener-views-table",
    "PAGINATION": "pageSelect",
    "PAGINATION_NAV": "screener_pagination",
}

# for faster processing flattening instead of lookup 
INV_HASH = {item: category for category, items in SITE_INVENTORY.items() for item in items}

BASE_URL = "https://finviz.com/"

ETF = {
    "name": "ETF_SCREENER_AGGREGATE",
    "first_page": "https://finviz.com/screener.ashx?v=181",
    "string_pattern": "screener.ashx?v=181&r=" # etf finviz
    "dom_mapping": {
        6: ['price', 'ticker', 'company', 'industry', 'value', 'country'],
        5: ["dividend"],
        7: ["change_pct"]
    }
}

AUM = {
    "name": "AUM_SCREENER_AGGREGATE",
    "first_page": "https://finviz.com/screener?v=191",
    "string_pattern": "screener?v=191&r=", # aum finviz
    "dom_mapping": None,
    }

