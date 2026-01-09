
# columns to delete from specific source data
SRC_DELETE_COLS = {
    "dripinvesting" : {
        "Logo",
    },
}

SRC_TO_SCHEMA_COL_NAME = {
    "dripinvesting" : {
        "Logo" : "ok",
    },
}


class DataSource:

    def __init__(self):
        self._col_to_schema_name = {}
        self._col_allowed_symbols = {}
        self._col_convert_col_name = {}
        self._col_convert_factor = {}

    def get_col_schema_name(self, src_col_name):
        return self._col_to_schema_name.get(src_col_name, src_col_name)

    def get_col_allowed_symbols(self, src_col_name):
        raise NotImplementedError

    def get_col_convert_col_name(self, src_col_name):
        raise NotImplementedError

    def get_col_convert_factor(self, src_col_name):
        raise NotImplementedError


class SourceDripInvesting(DataSource):
    def __init__(self):
        pass




class SupportedDataSources:
    DRIPINVESTING = "dripinvesting"


class SourceFactory:

    SRC_DEFS = {
        "dripinvesting" : SourceDripInvesting
    }

    @staticmethod
    def get_source(src_name):
        return SourceFactory.SRC_DEFS[src_name]()
