from schema import SchemaColumns


class SupportedDataSources:
    DRIPINVESTING = "dripinvesting"


class DataSource:

    def __init__(self):
        self._name = None
        self._delete_cols = {}
        self._schema_col_names = {}
        self._col_allowed_symbols = {}
        self._col_convert_col_name = {}
        self._col_convert_factor = {}

    def get_name(self):
        return self._name

    def get_col_names(self):
        return self._schema_col_names.items()

    def get_delete_cols(self):
        return self._delete_cols

    def get_col_schema_name(self, src_col_name):
        return self._col_to_schema_name.get(src_col_name, src_col_name)

    def get_col_allowed_symbols(self, src_col_name):
        return self._col_allowed_symbols.get(src_col_name, ())

    def get_col_convert_col_name(self, src_col_name):
        return self._col_convert_col_name.get(src_col_name, None)

    def get_col_convert_factor(self, src_col_name):
        return self._col_convert_factor.get(src_col_name, None)


class SourceDripInvesting(DataSource):
    def __init__(self):

        self._name = SupportedDataSources.DRIPINVESTING

        self._delete_cols = {
            "Logo"
        }

        self._schema_col_names = {
            "Symbol" : SchemaColumns.SYMBOL,
            "Stock Type" : SchemaColumns.STOCK_TYPE,
            "Company" : SchemaColumns.COMPANY,
            "Sector" : SchemaColumns.SECTOR,
            "Industry" : SchemaColumns.INDUSTRY,
            "Price": SchemaColumns.PRICE,
            "Div Yield" : SchemaColumns.YIELD_1Y,
            "5Y Avg Yield" : SchemaColumns.YIELD_5Y,
            "Current Div" : SchemaColumns.CUR_DIV,
            "Payouts/Year": SchemaColumns.NUM_DIV_1Y,
            "Annualized" : SchemaColumns.DIV_1Y,
            "Previous Div" : SchemaColumns.PREV_DIV,
            "Ex-Date" : SchemaColumns.EX_DATE,
            "Pay-Date": SchemaColumns.PAY_DATE,
            "Low" : SchemaColumns.PRICE_LOW,
            "High" : SchemaColumns.PRICE_HIGH,
            "Chowder Number": SchemaColumns.CHOWDER,
            "DGR 1Y": SchemaColumns.DGR_1Y,
            "DGR 3Y" : SchemaColumns.DGR_3Y,
            "DGR 5Y": SchemaColumns.DGR_5Y,
            "DGR 10Y": SchemaColumns.DGR_10Y,
            "TTR 1Y" : SchemaColumns.TTR_1Y,
            "TTR 3Y" : SchemaColumns.TTR_3Y,
            "FV (Peter Lynch)" : SchemaColumns.FAIR_PRICE,
            "FV (Peter Lynch) %" : SchemaColumns.FAIR_VALUE,
            "EPS 1Y" : SchemaColumns.EPS_1Y,
            "Revenue 1Y" : SchemaColumns.REVENUE_1Y,
            "NPM" : SchemaColumns.NPM,
            "CF/Share" : SchemaColumns.CF_SHARE,
            "ROE" : SchemaColumns.ROE,
            "Current R" : SchemaColumns.CUR_R,
            "Debt/Capital" : SchemaColumns.DEBT_CAPITAL,
            "ROTC" : SchemaColumns.ROTC,
            "P/E" : SchemaColumns.P_E,
            "P/BV" : SchemaColumns.P_BV,
            "PEG" : SchemaColumns.PEG,
        }


        self._col_allowed_symbols = {}
        self._col_convert_col_name = {}
        self._col_convert_factor = {}



class SourceFactory:

    SRC_DEFS = {
        "dripinvesting" : SourceDripInvesting
    }

    @staticmethod
    def get_source(src_name):
        return SourceFactory.SRC_DEFS[src_name]()
