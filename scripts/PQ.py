import pandas as pd
from pandas.plotting import scatter_matrix as pdsm 
import pathlib
from collections.abc import Iterable
import plotly.express as px
import plotly.graph_objects as go
from PK import *
from configparser import ConfigParser
import numpy as np

# catch sklearn verbose warnings
import warnings
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)
from sklearn import datasets, linear_model
from sklearn.utils import estimator_html_repr
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import KBinsDiscretizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.compose import make_column_transformer
from sklearn.compose import ColumnTransformer
from sklearn.compose import make_column_selector as selector
from sklearn.impute import SimpleImputer
from sklearn.svm import LinearSVC
from sklearn.linear_model import RidgeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA, NMF
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import make_scorer
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.metrics import precision_recall_curve, auc
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.feature_selection import VarianceThreshold
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
# vizualize pipeline
from sklearn import set_config
set_config(display='diagram')  
# for sklearn transformer caching
from tempfile import mkdtemp
from shutil import rmtree
import pickle

# ## PQ CLASS - QUERY INTERFACE ###

class SOURCE(object):
    
    def __init__(self, source):
        super(SOURCE, self).__init__()
        file_ext = pathlib.Path(source).suffix
        self._config = ConfigParser()
        self._config.read('config.ini', encoding='utf_8')
            
        # config.ini 'kintone app' section
        if source in self._config.sections() and 'kintone_domain' in self._config[source]:
            domain = self._config.get(source,'kintone_domain')
            app_id = self._config.getint(source,'app_id')
            api_token = self._config.get(source,'api_token')
            model_csv = self._config.get(source,'model_csv')
        
            m = jsModelFactory.get(model_csv)
            js = JinSapo(domain=domain, app_id=app_id, api_token=api_token, model=m)
            self._df = js.select_df()
        
        # config.ini 'csv' section
        elif source in self._config.sections() and 'csv' in self._config[source]:
            self._df = pd.read_csv(self._config[source]['csv'])
            
        # config.ini 'xlsx' section
        elif source in self._config.sections() and 'xlsx' in self._config[source]:
            self._df = pd.read_csv(self._config[source]['xlsx'])
        
        # csv
        elif file_ext == '.csv':
            self._df = pd.read_csv(source)
            
        # excel
        elif file_ext == '.xlsx':
            self._df = pd.read_excel(source)
        
        else:
            self._df = pd.DataFrame()
        self._showFig = False
        self._preview = 'no_chart' #'current_chart' 'all_charts' 'full' 'color_swatches'
        self._colorSwatch = px.colors.qualitative.Plotly
        
        self._figs = []
        
        self._fig_config =  {
            'displaylogo': False,
            'toImageButtonOptions': {
                'format': 'png', # one of png, svg, jpeg, webp
                'filename': 'custom_image',
                'height': None,
                'width': None,
                'scale': 5 # Multiply title/legend/axis/canvas sizes by this factor
            },
            'edits': {
                'axisTitleText': True,
                'legendPosition': True,
                'legendText': True,
                'titleText': True,
                'annotationPosition': True,
                'annotationText': True
            }
        }
        # format floats as percentages for readability
        #pd.options.display.float_format = '{:.2%}'.format
        
    def _repr_pretty_(self, p, cycle): 
        if self._preview == 'current_chart':
            return self._figs[-1].show(config=self._fig_config), display(self._df)
        elif self._preview == 'all_charts':
            return tuple([f.show(config=self._fig_config) for f in self._figs]), display(self._df)
        elif self._preview == 'full':
            return tuple([f.show(config=self._fig_config) for f in self._figs]), display(self._df), display(self._df.info())
        elif self._preview == 'color_swatches':
            return px.colors.qualitative.swatches().show(), display(self._df)
        elif isinstance(self._preview, int):
            return tuple([f.show(config=self._fig_config) for f in self._figs[-self._preview:]]), display(self._df)
        else:
            return display(self._df)
        
    def __repr__(self): 
        return self._df.__repr__()
    
    def __str__(self): 
        return self._df.__str__()
    
    def _fig(self, fig = None, preview = 'no_chart'):
        if fig == None:
            self._preview = preview
        else:
            self._figTidy(fig)
            self._figs.append(fig)
            self._preview = 'current_chart'
            
    def _figTidy(self, fig):
        #fig.update_traces()
        fig.update_layout(
            overwrite=True,
            #colorway=self._colorSwatch,
            dragmode='drawopenpath',
            #newshape_line_color='cyan',
            #title_text='Draw a path to separate versicolor and virginica',
            modebar_add=['drawline',
                'drawcircle',
                'drawrect',
                'eraseshape',
                'pan2d'
            ],
            modebar_remove=['resetScale', 'lasso2d'] #'select', 'zoom', 
        )
        #fig.update_annotations()
        #fig.update_xaxes()
            
    # DATAFRAME 'COLUMN' ACTIONS
    
    def DF_COL_ADD_FIXED(self, value, name = 'new_column', data_frame=None):
        '''Add a new column with a 'fixed' value as content'''
        if data_frame is None: data_frame = self._df
        name = self._toUniqueColName(name)
        data_frame[name] = value
        self._fig()
        return self
    
    def DF_COL_ADD_INDEX(self, name = 'new_column', start = 1, data_frame=None):
        '''Add a new column with a index/serial number as content'''
        if data_frame is None: data_frame = self._df
        name = self._toUniqueColName(name, data_frame=data_frame)
        data_frame[name] = range(start, data_frame.shape[0] + start)
        self._fig()
        return self
    
    def DF_COL_ADD_INDEX_FROM_0(self, name = 'new_column', data_frame=None):
        '''Convenience method for DF_COL_ADD_INDEX'''
        self.DF_COL_ADD_INDEX(name, start = 0, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COL_ADD_INDEX_FROM_1(self, name = 'new_column', data_frame=None):
        '''Convenience method for DF_COL_ADD_INDEX'''
        self.DF_COL_ADD_INDEX(name, start = 1, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COL_ADD_CUSTOM(self, column, lmda, name = 'new_column', data_frame=None):
        '''Add a new column with custom (lambda) content'''
        if data_frame is None: data_frame = self._df
        name = self._toUniqueColName(name, data_frame=data_frame)
        data_frame[name] = data_frame[column].apply(lmda)
        self._fig()
        return self
    
    def DF_COL_ADD_EXTRACT_POSITION_AFTER(self, column, pos, name = 'new_column', data_frame=None):
        '''Add a new column with content extracted from after char pos in existing column'''
        self.DF_COL_ADD_CUSTOM(column, lambda x: x[pos:], name = name, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COL_ADD_EXTRACT_POSITION_BEFORE(self, column, pos, name = 'new_column', data_frame=None):
        '''Add a new column with content extracted from before char pos in existing column'''
        self.DF_COL_ADD_CUSTOM(column, lambda x: x[:pos], name = name, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COL_ADD_EXTRACT_CHARS_FIRST(self, column, chars, name = 'new_column', data_frame=None):
        '''Add a new column with first N chars extracted from column'''
        self.DF_COL_ADD_CUSTOM(column, lambda x: x[:chars], name = name, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COL_ADD_EXTRACT_CHARS_LAST(self, column, chars, name = 'new_column', data_frame=None):
        '''Add a new column with last N chars extracted from column'''
        self.DF_COL_ADD_CUSTOM(column, lambda x: x[-chars:], name = name, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COL_ADD_DUPLICATE(self, column, name = 'new_column', data_frame=None):
        '''Add a new column by copying an existing column'''
        if data_frame is None: data_frame = self._df
        name = self._toUniqueColName(name, data_frame=data_frame)
        data_frame[name] = data_frame[column]
        self._fig()
        return self
    
    def DF_COL_DELETE(self, columns, data_frame=None):
        '''Delete specified column/s'''
        if data_frame is None: data_frame = self._df
        columns = self._colHelper(columns, data_frame=data_frame)
        data_frame = data_frame.drop(columns, axis = 1)
        self._fig()
        return self
    
    def DF_COL_DELETE_EXCEPT(self, columns, data_frame=None):
        '''Deleted all column/s except specified'''
        if data_frame is None: data_frame = self._df
        columns = self._colHelper(columns, data_frame=data_frame)
        cols = self._removeElementsFromList(data_frame.columns.values.tolist(), columns)
        self.DF_COL_DELETE(cols, data_frame=data_frame)
        self.DF_COL_MOVE_TO_FRONT(columns, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COL_MOVE_TO_FRONT(self, columns, data_frame=None):
        '''Move specified column/s to new index'''
        if data_frame is None: data_frame = self._df
        colsToMove = self._colHelper(columns, data_frame=data_frame)
        otherCols = self._removeElementsFromList(data_frame.columns.values.tolist(), colsToMove)
        data_frame = data_frame[colsToMove + otherCols]
        self._fig()
        return self
    
    def DF_COL_MOVE_TO_BACK(self, columns, data_frame=None):
        '''Move specified column/s to new index'''
        if data_frame is None: data_frame = self._df
        colsToMove = self._colHelper(columns, data_frame=data_frame)
        otherCols = self._removeElementsFromList(data_frame.columns.values.tolist(), colsToMove)
        data_frame = data_frame[otherCols + colsToMove]
        self._fig()
        return self
    
    def DF_COL_RENAME(self, columns, data_frame=None):
        '''Rename specfied column/s'''
        if data_frame is None: data_frame = self._df
        # we handle dict for all or subset, OR list for all
        if isinstance(columns, dict):
            data_frame.rename(columns = columns, inplace = True)
        else:
            data_frame.columns = columns
        self._fig()
        return self
    
    #col_reorder list of indices, list of colnames
    
    def DF_COL_FORMAT_TO_UPPERCASE(self, columns = None, data_frame=None):
        '''Format specified column/s values to uppercase'''
        if data_frame is None: data_frame = self._df
        if columns == None: columns = data_frame.columns.values.tolist()
        data_frame[columns] = data_frame[columns].apply(lambda s: s.str.upper(), axis=0)
        self._fig()
        return self
    
    def DF_COL_FORMAT_TO_LOWERCASE(self, columns = None, data_frame=None):
        '''Format specified column/s values to lowercase'''
        if data_frame is None: data_frame = self._df
        if columns == None: columns = data_frame.columns.values
        data_frame[columns] = data_frame[columns].apply(lambda s: s.str.lower(), axis=0)
        self._fig()
        return self
    
    def DF_COL_FORMAT_TO_TITLECASE(self, columns = None, data_frame=None):
        '''Format specified column/s values to titlecase'''
        if data_frame is None: data_frame = self._df
        if columns == None: columns = data_frame.columns.values
        data_frame[columns] = data_frame[columns].apply(lambda s: s.str.title(), axis=0)
        self._fig()
        return self
    
    def DF_COL_FORMAT_STRIP(self, columns = None, data_frame=None):
        '''Format specified column/s values by stripping invisible characters'''
        if data_frame is None: data_frame = self._df
        if columns == None: columns = data_frame.columns.values
        data_frame[columns] = data_frame[columns].apply(lambda s: s.str.strip(), axis=0)
        self._fig()
        return self
    
    def DF_COL_FORMAT_STRIP_LEFT(self, columns = None, data_frame=None):
        '''Convenience method for DF_COL_FORMAT_STRIP'''
        if data_frame is None: data_frame = self._df
        if columns == None: columns = data_frame.columns.values
        data_frame[columns] = data_frame[columns].apply(lambda s: s.str.lstrip(), axis=0)
        self._fig()
        return self
    
    def DF_COL_FORMAT_STRIP_RIGHT(self, columns = None, data_frame=None):
        '''Convenience method for DF_COL_FORMAT_STRIP'''
        if data_frame is None: data_frame = self._df
        if columns == None: columns = data_frame.columns.values
        data_frame[columns] = data_frame[columns].apply(lambda s: s.str.rstrip(), axis=0)
        self._fig()
        return self
    
    def DF_COL_FORMAT_ADD_PREFIX(self, prefix, column, data_frame=None):
        '''Format specified single column values by adding prefix'''
        if data_frame is None: data_frame = self._df
        data_frame[column] = str(prefix) + data_frame[column].astype(str)
        self._fig()
        return self
    
    def DF_COL_FORMAT_ADD_SUFFIX(self, suffix, column, data_frame=None):
        '''Format specified single column values by adding suffix'''
        data_frame[column] = data_frame[column].astype(str) + str(suffix)
        self._fig()
        return self
    
    def DF_COL_FORMAT_TYPE(self, columns, typ = 'str', data_frame=None):
        if data_frame is None: data_frame = self._df
        if columns == None: 
            data_frame = data_frame.astype(typ)
        else:
            convert_dict = {c:typ for c in columns}
            data_frame = data_frame.astype(convert_dict)
        self._fig()
        return self
    
    def DF_COL_FORMAT_ROUND(self, decimals, data_frame=None):
        '''Round numerical column values to specified decimal'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.round(decimals)
        self._fig()
        return self
    
    # DATAFRAME 'ROW' ACTIONS
    
    #def DF_ROW_ADD(self, row, index = 0):
    #    self._df.loc[index] = row
    #    self._showFig = False
    #    return self
    
    #def DF_ROW_DELETE(self, rowNums):
    #    pos = rowNums - 1
    #    self._df.drop(self._df.index[pos], inplace=True)
    #    self._showFig = False
    #    return self
    
    def DF_ROW_FILTER(self, criteria, data_frame=None):
        '''Filter rows with specified filter criteria'''
        if data_frame is None: data_frame = self._df
        data_frame.query(criteria, inplace = True)
        self._fig()
        return self
    
    def DF_ROW_KEEP_BOTTOM(self, numRows, data_frame=None):
        '''Delete all rows except specified bottom N rows'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.tail(numRows)
        self._fig()
        return self
    
    def DF_ROW_KEEP_TOP(self, numRows, data_frame=None):
        '''Delete all rows except specified top N rows'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.head(numRows)
        self._fig()
        return self
    
    def DF_ROW_REVERSE(self, data_frame=None):
        '''Reorder all rows in reverse order'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame[::-1].reset_index(drop = True)
        self._fig()
        return self
    
    def DF_ROW_SORT(self, columns, descending = False, data_frame=None):
        '''Reorder dataframe by specified columns in ascending/descending order'''
        if data_frame is None: data_frame = self._df
        ascending = 1
        if descending == True: ascending = 0
        data_frame = data_frame.sort_values(by = columns, axis = 0, ascending = ascending, na_position ='last')
        self._fig()
        return self
    
    # DATAFRAME ACTIONS
    
    def DF__APPEND(self, otherdf, data_frame=None):
        '''Append a table to bottom of current table'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.append(otherdf, ignore_index=True)
        self._fig()
        return self
    
    def DF__FILL_DOWN(self, data_frame=None):
        '''Fill blank cells with values from last non-blank cell above'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.fillna(method="ffill", axis = 'index', inplace = True)
        self._fig()
        return self
    
    def DF__FILL_UP(self, data_frame=None):
        '''Fill blank cells with values from last non-blank cell below'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.fillna(method="bfill", axis = 'index', inplace = True)
        self._fig()
        return self
    
    def DF__FILL_RIGHT(self, data_frame=None):
        '''Fill blank cells with values from last non-blank cell from left'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.fillna(method="ffill", axis = 'columns', inplace = True)
        self._fig()
        return self
    
    def DF__FILL_LEFT(self, data_frame=None):
        '''Fill blank cells with values from last non-blank cell from right'''
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.fillna(method="bfill", axis = 'columns', inplace = True)
        self._fig()
        return self
    
    def DF__GROUP(self, groupby, aggregates = None, data_frame=None):
        '''Group table contents by specified columns with optional aggregation (sum/max/min etc)'''
        if data_frame is None: data_frame = self._df
        if aggregates == None:
            data_frame = data_frame.groupby(groupby, as_index=False).first()
        else:
            data_frame = data_frame.groupby(groupby, as_index=False).agg(aggregates)
            data_frame.columns = ['_'.join(col).rstrip('_') for col in data_frame.columns.values]
        self._fig()
        return self
    
    def DF__MERGE(self, otherdf, on, how = 'left', data_frame=None):
        if data_frame is None: data_frame = self._df
        data_frame = pd.merge(data_frame, otherdf, on=on, how=how)
        self._fig()
        return self
    
    def DF__REPLACE(self, before, after, data_frame=None):
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.apply(lambda s: s.str.replace(before, after, regex=False), axis=0)
        self._fig()
        return self
    
    def TAB_TRANSPOSE(self, data_frame=None):
        if data_frame is None: data_frame = self._df
        data_frame.transpose()
        self._fig()
        return self
    
    def DF__UNPIVOT(self, indexCols, data_frame=None):
        if data_frame is None: data_frame = self._df
        data_frame = pd.melt(data_frame, id_vars = indexCols)
        self._fig()
        return self
    
    def DF__PIVOT(self, indexCols, cols, vals, data_frame=None):
        #indexCols = list(set(df.columns) - set(cols) - set(vals))
        if data_frame is None: data_frame = self._df
        data_frame = data_frame.pivot(index = indexCols, columns = cols, values = vals).reset_index().rename_axis(mapper = None,axis = 1)
        self._fig()
        return self
    
    def DF_COLHEADER_PROMOTE(self, row = 1, data_frame=None):
        '''Promote row at specified index to column headers'''
        if data_frame is None: data_frame = self._df
        # make new header, fill in blank values with ColN
        i = row - 1
        newHeader = data_frame.iloc[i:row].squeeze()
        newHeader = newHeader.values.tolist()
        for i in newHeader:
            if i == None: i = 'Col'
        # set new col names
        self.DF_COL_RENAME(newHeader, data_frame=data_frame)
        
        # delete 'promoted' rows
        self.DF_ROW_DELETE(row, data_frame=data_frame)
        
        self._fig()
        return self
    
    def DF_COLHEADER_DEMOTE(self, data_frame=None):
        '''Demote column headers to make 1st row of table'''
        if data_frame is None: data_frame = self._df
        # insert 'demoted' column headers
        self.DF_ROW_ADD(data_frame.columns)
        # make new header as Col1, Col2, Coln
        newHeader = ['Col' + str(x) for x in range(len(data_frame.columns))]
        # set new col names
        self.DF_COL_RENAME(newHeader, data_frame=data_frame)
        self._fig()
        return self
    
    def DF_COLHEADER_REORDER_ASC(self, data_frame=None):
        '''Reorder column titles in ascending order'''
        if data_frame is None: data_frame = self._df
        data_frame.columns = sorted(data_frame.columns.values.tolist())
        self._fig()
        return self
    
    def DF_COLHEADER_REORDER_DESC(self, data_frame=None):
        '''Reorder column titles in descending order'''
        if data_frame is None: data_frame = self._df
        data_frame.columns = sorted(data_frame.columns.values.tolist(), reverse = True)
        self._fig()
        return self
    
    def DF_COLHEADER_REORDER(self, columns, data_frame=None):
        '''Reorder column titles in specified order'''
        # if not all columns are specified, we order to front and add others to end
        self.DF_COL_MOVE_TO_FRONT(columns, data_frame=data_frame)
        self._fig()
        return self
    
    def DF__STATS(self, data_frame=None):
        '''Show basic summary statistics of table contents'''
        if data_frame is None: data_frame = self._df
        stats =  data_frame.describe().T
        stats.insert(0, 'Feature', stats.index)
        self.DF_COL_ADD_INDEX_FROM_1(name='No', data_frame=stats)
        self.DF_COL_MOVE_TO_FRONT(columns='No', data_frame=stats)
        self.VIZ_TABLE(x=stats.columns.values, data_frame=stats)
        self._fig(preview = 1)
        return self
    
    # VIZUALIZATION ACTIONS
    
    def VIZ_BOX(self, x=None, y=None, color=None, facet_col=None, facet_row=None, data_frame=None, **kwargs):
        '''Draw a box plot'''
        if data_frame is None: data_frame = self._df
        fig = px.box(data_frame=data_frame, x=x, y=y, color=color, facet_col=facet_col, facet_row=facet_row, 
                     color_discrete_sequence=self._colorSwatch, **kwargs)
        self._fig(fig)
        return self
        
    def VIZ_VIOLIN(self, x=None, y=None, color=None, facet_col=None, facet_row=None, data_frame=None, **kwargs):
        '''Draw a violin plot'''
        if data_frame is None: data_frame = self._df
        fig = px.violin(data_frame=data_frame, x=x, y=y, color=color, facet_col=facet_col, facet_row=facet_row, box=True, 
                     color_discrete_sequence=self._colorSwatch, **kwargs)
        self._fig(fig)
        return self
        
    def VIZ_HIST(self, x=None, color=None, facet_col=None, facet_row=None, data_frame=None, **kwargs):
        '''Draw a hisotgram'''
        if data_frame is None: data_frame = self._df
        fig = px.histogram(data_frame=data_frame, x=x, color=color, facet_col=facet_col, facet_row=facet_row, 
                     color_discrete_sequence=self._colorSwatch, **kwargs)
        self._fig(fig)
        return self
    
    def VIZ_HIST_LIST(self, color=None, data_frame=None, **kwargs):
        '''Draw a histogram for all fields in current dataframe'''
        if data_frame is None: data_frame = self._df
        for c in data_frame.columns:
            fig = px.histogram(data_frame=data_frame, x=c, color=color, color_discrete_sequence=self._colorSwatch, **kwargs)
            self._fig(fig)
        self._fig(preview = len(data_frame.columns))
        return self
    
    def VIZ_SCATTER(self, x=None, y=None, color=None, size=None, symbol=None, facet_col=None, facet_row=None, data_frame=None, **kwargs):
        '''Draw a scatter plot'''
        if data_frame is None: data_frame = self._df
        fig = px.scatter(data_frame=data_frame, x=x, y=y, color=color, size=size, symbol=symbol, facet_col=facet_col, facet_row=facet_row, 
                     color_discrete_sequence=self._colorSwatch, **kwargs)
        self._fig(fig)
        return self
        
    def VIZ_BAR(self, x=None, y=None, color=None, facet_col=None, facet_row=None, data_frame=None, **kwargs):
        '''Draw a bar plot'''
        if data_frame is None: data_frame = self._df
        fig = px.bar(data_frame=data_frame, x=x, y=y, color=color, facet_col=facet_col, facet_row=facet_row, 
                     color_discrete_sequence=self._colorSwatch, **kwargs)
        self._fig(fig)
        return self
    
    def VIZ_LINE(self, x=None, y=None, color=None, facet_col=None, facet_row=None, markers=True, data_frame=None, **kwargs):
        '''Draw a line plot'''
        if data_frame is None: data_frame = self._df
        fig = px.line(data_frame=data_frame, x=x, y=y, color=color, facet_col=facet_col, facet_row=facet_row, #markers=markers, 
                      color_discrete_sequence=self._colorSwatch, **kwargs)
        self._fig(fig)
        return self
    
    def VIZ_AREA(self, x=None, y=None, color=None, facet_col=None, facet_row=None, markers=True, data_frame=None, **kwargs):
        '''Draw a line plot'''
        if data_frame is None: data_frame = self._df
        fig = px.area(data_frame=data_frame, x=x, y=y, color=color, facet_col=facet_col, facet_row=facet_row, #markers=markers, 
                     color_discrete_sequence=self._colorSwatch, **kwargs)
        self._fig(fig)
        return self
    
    def VIZ_TREEMAP(self, path, values, root='All data', data_frame=None, **kwargs):
        '''Draw a treemap plot'''
        path = [px.Constant("All data")] + path
        if data_frame is None: data_frame = self._df
        fig = px.treemap(data_frame=data_frame, path=path, values=values, color_discrete_sequence=self._colorSwatch, **kwargs)
        fig.update_traces(root_color="lightgrey")
        fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
        self._fig(fig)
        return self
    
    def VIZ_SCATTERMATRIX(self, dimensions=None, color=None, data_frame=None, **kwargs):
        '''Draw a scatter matrix plot'''
        if data_frame is None: data_frame = self._df
        fig = px.scatter_matrix(data_frame=data_frame, dimensions=dimensions, color_discrete_sequence=self._colorSwatch, color=color, **kwargs)
        self._fig(fig)
        return self
    
    def VIZ_TABLE(self, x=None, data_frame=None, **kwargs):
        '''Draw a table'''
        if data_frame is None: data_frame = self._df
        
        cell_values = data_frame[x].to_numpy().T
        fig = go.Figure(data=[go.Table(
            header=dict(values=x,
                       align='left',
                       font_size=12,
                       height=30),
            cells=dict(values=cell_values,
                      align='left',
                       font_size=12,
                       height=30))
        ])
        self._fig(fig)
        return self
    
    # MACHINE LEARNING 'FEATURE SELECTION' ACTIONS
    
    def ML_SELECT_FEATURES_NONE_ZERO_VARIANCE(self, data_frame=None):
        '''Select numerical features / columns with non-zero variance'''
        self.DF_COL_DELETE_EXCEPT(self._selectFeatures(method='VarianceThreshold', data_frame=data_frame), data_frame=data_frame)
        self._fig(fig)
        return self
    
    def ML_SELECT_FEATURES_N_BEST(self, target, n=10, data_frame=None):
        '''Select best n numerical features / columns for classifying target column'''
        self.DF_COL_DELETE_EXCEPT(self._selectFeatures(method='SelectKBest', target=target, n=n, data_frame=data_frame), data_frame=data_frame)
        self._fig(fig)
        return self
    
    def _selectFeatures(self, method=None, target=None, n=10, data_frame=None):
        if data_frame is None: data_frame = self._df
        
        if method == 'VarianceThreshold':
            sel = VarianceThreshold() #remove '0 variance'
            x = data_frame[self._colHelper(type='number', data_frame=data_frame)]
            sel.fit_transform(x)
            return sel.get_feature_names_out().tolist()
        elif method == 'SelectKBest':
            sel = SelectKBest(k=n)
            x = data_frame[self._removeElementsFromList(self._colHelper(type='number', data_frame=data_frame), [target])]
            y = data_frame[target]
            sel.fit_transform(X=x, y=y)
            features = sel.get_feature_names_out().tolist()
            features.append(target)
            return features
    
    #@ignore_warnings
    def ML_TRAIN_AND_SAVE_CLASSIFIER(self, target, path='classifier.joblib', data_frame=None):
        '''Train several classification models & select the best one'''
        
        if data_frame is None: data_frame = self._df
        
        # BUILD MODEL
        
        # FEATURE TRANSFORMERS
        
        # temporary manual addition of method to SimpleImputer class
        SimpleImputer.get_feature_names_out = (lambda self, names=None:
                                       self.feature_names_in_)
        
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())])

        categorical_transformer = OneHotEncoder(handle_unknown='ignore')

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, selector(dtype_include='number')),
                ('cat', categorical_transformer, selector(dtype_include=['object', 'category']))])

        # PIPELINE
        
        # prepare cache
        cachedir = mkdtemp()
        
        # Append classifier to preprocessing pipeline.
        # Now we have a full prediction pipeline.
        clf = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('classifier', LogisticRegression())
        ], memory=cachedir)
        
        param_grid = {
            'preprocessor__num__imputer__strategy': ['mean', 'median'],
            'classifier__C': [0.1, 1.0, 10, 100],
        }
        
        # SCORERS
        
        # The scorers can be either one of the predefined metric strings or a scorer
        # callable, like the one returned by make_scorer
        scoring = {
            'AUC': 'roc_auc', 
            'Accuracy': make_scorer(accuracy_score)
        }
        
        # BUILD GRID FOR PARAM SEARCH
        
        # Setting refit='AUC', refits an estimator on the whole dataset with the
        # parameter setting that has the best cross-validated AUC score.
        # That estimator is made available at ``gs.best_estimator_`` along with
        # parameters like ``gs.best_score_``, ``gs.best_params_`` and
        # ``gs.best_index_``
        
        grid = GridSearchCV(clf,
                            n_jobs=1, 
                            param_grid=param_grid, 
                            cv=10,
                            scoring=scoring, 
                            refit='AUC', 
                            return_train_score=True)
        
        # SPLIT & FIT!
        
        train_df, test_df = train_test_split(data_frame, test_size=0.2, random_state=0)
        grid.fit(train_df.drop(target, axis=1), train_df[target])
        
        
        # after hard work of model fitting, we can clear pipeline/transformer cache
        rmtree(cachedir)
        
        # SAVE/'PICKLE' MODEL
        
        # generate path
        if path in self._config.sections() and 'model' in self._config[path]:
            path = self._config[path]['model']
        
        # save
        from joblib import dump
        dump(grid.best_estimator_, path, compress = 1) 
        
        # force evaluation
        self._ML_EVAL_CLASSIFIER(path, target, test_df, train_df, pos_label='Yes')
        return self
    
    def ML_EVAL_CLASSIFIER(self, target, path='classifier.joblib', pos_label='Yes', data_frame=None):
        '''Evaluate a classfier with TEST data'''
        if data_frame is None: data_frame = self._df
        self._ML_EVAL_CLASSIFIER(path, target, test_df=data_frame, trainf_df=None, pos_label=pos_label)
        return self
        
    def _ML_EVAL_CLASSIFIER(self, path, target, test_df, train_df, pos_label, **kwargs):
        '''Draw a ROC plot'''
        
        # generate path
        if path in self._config.sections() and 'model' in self._config[path]:
            path = self._config[path]['model']
            
        from joblib import load
        # load saved model again to be sure
        clf = load(path) 
        
        #PREPARE DATA
        
        # X, y columns
        X, y = self._removeElementsFromList(list(test_df.columns), target), target
        
        # test
        test_df['Split'] = 'test'
        test_df['Prediction'] = clf.predict(test_df[X])
        test_df['Score'] = clf.predict_proba(test_df[X])[:, 1]
        
        # train
        train_df['Split'] = 'train'
        train_df['Prediction'] = clf.predict(train_df[X])
        train_df['Score'] = clf.predict_proba(train_df[X])[:, 1]
        
        # combined test/train
        eval_df = test_df.append(train_df)
        
        # separately add count column, sort
        test_df.sort_values(by = 'Score', inplace=True)
        test_df.insert(0, 'Count', range(1, test_df.shape[0] + 1))
        train_df.sort_values(by = 'Score', inplace=True)
        train_df.insert(0, 'Count', range(1, train_df.shape[0] + 1))
        eval_df.sort_values(by = 'Score', inplace=True)
        eval_df.insert(0, 'Count', range(1, eval_df.shape[0] + 1))
        
        # CONFUSION MATRIX
        # use test
        np = confusion_matrix(test_df[y], test_df['Prediction'], labels=['No', 'Yes'], normalize='all')
        df = pd.DataFrame(data=np.ravel(), columns=['value']) 
        df['true'] = ['Negative', 'Negative', 'Positive', 'Positive']
        df['name'] = ['True negative', 'False Positive', 'False negative', 'True positive']
        
        # show confusion matrix as 'treemap'
        self.VIZ_TREEMAP(data_frame=df, 
                         path=['true', 'name'], 
                         values='value',
                         root='Top',
                         #width=600,
                         #height=450,
                         title='Classification Results (Confusion Matrix)')
        
        # table of actual target, classifier scores and predictions based on those scores: use test
        self.VIZ_TABLE(data_frame=test_df,
                      x=['Count', y, 'Score', 'Prediction'], 
                      )
        self._figs[-1].update_layout(
            title="Classification Results (Details)",
            width=600, 
            height=450,
        ) 
        
        # histogram of scores compared to true labels: use test
        self.VIZ_HIST(data_frame=test_df,
                      title='Classifier score vs True labels',
                      x='Score', 
                      color=target,
                      height=400,
                      nbins=50, 
                      labels=dict(color='True Labels', x='Classifier Score')
                     )
        
        # preliminary viz & roc
        fpr, tpr, thresholds = roc_curve(test_df[y], test_df['Score'], pos_label=pos_label)
        
        # tpr, fpr by threshold chart
        df = pd.DataFrame({
            'False Positive Rate': fpr,
            'True Positive Rate': tpr
        }, index=thresholds)
        df.index.name = "Thresholds"
        df.columns.name = "Rate"
        
        self.VIZ_LINE(data_frame=df, 
                      title='True Positive Rate and False Positive Rate at every threshold', 
                      width=600, 
                      height=450,
                      range_x=[0,1], 
                      range_y=[0,1],
                      markers=False
                     )
        
        # roc chart
        self.VIZ_AREA(x=fpr, y=tpr,
                      #title=f'ROC Curve (AUC: %.2f)'% roc_auc_score(y_test, y_score),
                      width=600, 
                      height=450,
                      labels=dict(x='False Positive Rate', y='True Positive Rate'),
                      range_x=[0,1], 
                      range_y=[0,1],
                      markers=False
                     )
        
        self._figs[-1].add_shape(type='line', line=dict(dash='dash', color='firebrick'),x0=0, x1=1, y0=0, y1=1)

        precision, recall, thresholds = precision_recall_curve(test_df[target], test_df['Score'], pos_label=pos_label)

        # precision/recall chart
        self.VIZ_AREA(x=recall, y=precision,
                      title=f'Precision-Recall Curve (AUC={auc(fpr, tpr):.4f})',
                      width=600, 
                      height=450,
                      labels=dict(x='Recall', y='Precision'),
                      range_x=[0,1], 
                      range_y=[0,1],
                      markers=False)
        
        self._figs[-1].add_shape(type='line', line=dict(dash='dash', color='firebrick'),x0=0, x1=1, y0=0, y1=1)
        
        self._fig(preview = 6)
        return
        
    
    # MACHINE LEARNING 'MODEL TRAINING' ACTIONS
    
    #@ignore_warnings
    def ML_TRAIN_AND_SAVE_REGRESSOR(self, target, path='classifier.joblib', data_frame=None):
        '''Train several classification models & select the best one'''
        
        if data_frame is None: data_frame = self._df
        
        # BUILD MODEL
        
        # FEATURE TRANSFORMERS    
        # temporary manual addition of method to SimpleImputer class
        SimpleImputer.get_feature_names_out = (lambda self, names=None:
                                       self.feature_names_in_)
        
        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())])

        categorical_transformer = OneHotEncoder(handle_unknown='ignore')

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, selector(dtype_include='number')),
                ('cat', categorical_transformer, selector(dtype_include=['object', 'category']))])

        # PIPELINE
        
        # prepare cache
        cachedir = mkdtemp()
        
        # Append classifier to preprocessing pipeline.
        # Now we have a full prediction pipeline.
        clf = Pipeline(steps=[
            ('preprocessor', preprocessor),
            #('classifier', LogisticRegression())
            ('regressor',  LinearRegression())
        ], memory=cachedir)
        
        param_grid = {
            'preprocessor__num__imputer__strategy': ['mean', 'median'],
            #'classifier__C': [0.1, 1.0, 10, 100],
        }
        
        # SCORERS
        
        # The scorers can be either one of the predefined metric strings or a scorer
        # callable, like the one returned by make_scorer
        scoring = {
            'Mean_squared_error': 'neg_mean_squared_error',
            'r2': 'r2'
        }
        
        # BUILD GRID FOR PARAM SEARCH
        
        # Setting refit='AUC', refits an estimator on the whole dataset with the
        # parameter setting that has the best cross-validated AUC score.
        # That estimator is made available at ``gs.best_estimator_`` along with
        # parameters like ``gs.best_score_``, ``gs.best_params_`` and
        # ``gs.best_index_``
        
        grid = GridSearchCV(clf,
                            n_jobs=1, 
                            param_grid=param_grid, 
                            cv=10,
                            scoring=scoring, 
                            refit='r2', 
                            return_train_score=True)
        
        # PREPARE DATA & FIT!
        
        train_df, test_df = train_test_split(data_frame, test_size=0.2, random_state=0)
        grid.fit(train_df.drop(target, axis=1), train_df[target])
        
        # after hard work of model fitting, we can clear pipeline/transformer cache
        rmtree(cachedir)
        
        # SAVE/'PICKLE' MODEL
        
        # generate path
        if path in self._config.sections() and 'model' in self._config[path]:
            path = self._config[path]['model']
        
        # save
        from joblib import dump
        dump(grid.best_estimator_, path, compress = 1) 
        
        # force evaluation
        #return self._ML_EVAL_REGRESSOR(path, X_test, y_test, X_train, y_train)
        self._ML_EVAL_REGRESSOR(path, target=target, test_df=test_df, train_df=train_df)
        return self
    
    def ML_EVAL_REGRESSOR(self, target, path='classifier.joblib'):
        '''Evaluate a regressor with TEST data'''
        # separate features, target
        self._ML_EVAL_REGRESSOR(path, target, test_df=self._df, train_df=None)
        return self
        
    def _ML_EVAL_REGRESSOR(self, path, target, test_df, train_df, **kwargs):
        '''Evaluate a regressor'''
        
        # generate path
        if path in self._config.sections() and 'model' in self._config[path]:
            path = self._config[path]['model']
            
        from joblib import load
        # load saved model again to be sure
        clf = load(path) 
        
        # PREPARE DATA
        
        # X, y columns
        X, y = self._removeElementsFromList(list(test_df.columns), target), target
        
        # test
        test_df['Split'] = 'test'
        test_df['Prediction'] = clf.predict(test_df[X])
        test_df['Residual'] = test_df['Prediction'] - test_df[y]
        
        # train
        train_df['Split'] = 'train'
        train_df['Prediction'] = clf.predict(train_df[X])
        train_df['Residual'] = train_df['Prediction'] - train_df[y]
        
        # combined test/train
        eval_df = test_df.append(train_df)
        
        # separately add count column, sort
        test_df.sort_values(by = 'Prediction', inplace=True)
        test_df.insert(0, 'Count', range(1, test_df.shape[0] + 1))
        train_df.sort_values(by = 'Prediction', inplace=True)
        train_df.insert(0, 'Count', range(1, train_df.shape[0] + 1))
        eval_df.sort_values(by = 'Prediction', inplace=True)
        eval_df.insert(0, 'Count', range(1, eval_df.shape[0] + 1))
                
        #PREDICTIONS VS ACTUAL
        # scatter: use combined test/train
        self.VIZ_SCATTER(data_frame=eval_df,
                         x=y,
                         y='Prediction',
                         title='Predicted ' + y + ' vs actual ' + y,
                         width=800,
                         height=600,
                         labels={target: 'Actual '+y, 'Prediction': 'Predicted '+y},
                         marginal_x='histogram', marginal_y='histogram',
                         trendline='ols',
                         color='Split'
                         #opacity=0.65
                        )
        self._figs[-1].add_shape(
           type="line", line=dict(dash='dash'),
           x0=eval_df[y].min(), y0=eval_df[y].min(),
           x1=eval_df[y].max(), y1=eval_df[y].max()
        )
        self._figs[-1].update_yaxes(nticks=10).update_xaxes(nticks=10)
        
        # table of actual target, classifier scores and predictions based on those scores: use test
        self.VIZ_TABLE(data_frame=test_df,
                      x=['Count', y, 'Prediction', 'Residual'], 
                      )
        self._figs[-1].update_layout(
            title="Regression Results (Details)",
            width=600, 
            height=450,
        )
        
        #RESIDUALS
        # use combined train/test
        self.VIZ_SCATTER(data_frame=eval_df,
                         x='Prediction',
                         y='Residual',
                         title='Gap between predicted '+y +' and actual '+ y,
                         labels={'Prediction': 'Predicted '+y, 'Residual': 'Gap (predicted - actual)'},
                         width=800,
                         height=600,
                         marginal_y='violin',
                         trendline='ols',
                         color='Split'
                         #opacity=0.65
                        )
        self._figs[-1].update_yaxes(nticks=10).update_xaxes(nticks=10)
        
        # COEFFICIENT/S
        
        # use test
        
        if(len(test_df[X]) == 1):
            df = pd.DataFrame({
                'X': test_df[X].to_numpy(),
                'y': test_df[y].to_numpy()
                #'X': X_test.iloc[:, 0].to_numpy(),
                #'y': y_test.to_numpy()
            })
            self.VIZ_SCATTER(data_frame=df,
                             x='X',
                             y='y',
                          title='Regression plot (r2: TBD)',
                          width=600, 
                          height=450
                        )
            # add prediction line
            x_range = test_df[X].sort_values(by=X)
            y_range = clf.predict(x_range)
            self._figs[-1].add_traces(go.Scatter(x=x_range.iloc[:, 0].to_numpy(), y=y_range, name='Regression Fit'))
        
        else:
            df = pd.DataFrame({
                'X': clf.named_steps['preprocessor'].get_feature_names_out(),
                'y': clf.named_steps['regressor'].coef_
            })
            colors = ['Positive' if c > 0 else 'Negative' for c in clf.named_steps['regressor'].coef_]
            self.VIZ_BAR(
                x='X', 
                y='y',
                data_frame=df,
                color=colors,
                width=1200,
                height=600,
                #color_discrete_sequence=['red', 'blue'],
                labels=dict(x='Feature', y='Linear coefficient'),
                title='Weight of each feature when predicting '+target
            )
        
        self._fig(preview = 4)
        return
    
    @property
    def REPORT_SET_VIZ_COLORS_PLOTLY(self):
        '''Set plot/report colors to 'Plotly'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Plotly)
    
    @property
    def REPORT_SET_VIZ_COLORS_D3(self):
        '''Set plot/report colors to 'D3'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.D3)
    
    @property
    def REPORT_SET_VIZ_COLORS_G10(self):
        '''Set plot/report colors to 'G10'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.G10)
    
    @property
    def REPORT_SET_VIZ_COLORS_T10(self):
        '''Set plot/report colors to 'T10'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.T10)
    
    @property
    def REPORT_SET_VIZ_COLORS_ALPHABET(self):
        '''Set plot/report colors to 'Alphabet'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Alphabet)
    
    @property
    def REPORT_SET_VIZ_COLORS_DARK24(self):
        '''Set plot/report colors to 'Dark24'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Dark24)
    
    @property
    def REPORT_SET_VIZ_COLORS_LIGHT24(self):
        '''Set plot/report colors to 'Light24'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Light24)
    
    @property
    def REPORT_SET_VIZ_COLORS_SET1(self):
        '''Set plot/report colors to 'Set1'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Set1)
    
    @property
    def REPORT_SET_VIZ_COLORS_PASTEL1(self):
        '''Set plot/report colors to 'Pastel1'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Pastel1)
    
    @property
    def REPORT_SET_VIZ_COLORS_DARK2(self):
        '''Set plot/report colors to 'Dark2'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Dark2)
    
    @property
    def REPORT_SET_VIZ_COLORS_SET2(self):
        '''Set plot/report colors to 'Set2'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Set2)
    
    @property
    def REPORT_SET_VIZ_COLORS_PASTEL2(self):
        '''Set plot/report colors to 'Pastel2'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Pastel2)
    
    @property
    def REPORT_SET_VIZ_COLORS_SET3(self):
        '''Set plot/report colors to 'Set3'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Set3)
    
    @property
    def REPORT_SET_VIZ_COLORS_ANTIQUE(self):
        '''Set plot/report colors to 'Antique'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Antique)
    
    @property
    def REPORT_SET_VIZ_COLORS_BOLD(self):
        '''Set plot/report colors to 'Bold'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Bold)
    
    @property
    def REPORT_SET_VIZ_COLORS_PASTEL(self):
        '''Set plot/report colors to 'Pastel'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Pastel)
    
    @property
    def REPORT_SET_VIZ_COLORS_PRISM(self):
        '''Set plot/report colors to 'Prism'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Prism)
    
    @property
    def REPORT_SET_VIZ_COLORS_SAFE(self):
        '''Set plot/report colors to 'Safe'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Safe)
    
    @property
    def REPORT_SET_VIZ_COLORS_VIVID(self):
        '''Set plot/report colors to 'Vivid'''
        return self._REPORT_SET_VIZ_COLORS(px.colors.qualitative.Vivid)
    
    def _REPORT_SET_VIZ_COLORS(self, swatch = px.colors.qualitative.Plotly):
        self._colorSwatch = swatch
        #self._fig(preview = 'color_swatches')
        return self
    
    @property
    def REPORT_PREVIEW(self):
        self._fig(preview = 'all_charts')
        return self
    
    @property
    def REPORT_PREVIEW_FULL(self):
        self._fig(preview = 'full')
        return self
    
    def REPORT_SAVE_ALL(self, path = None):
        self.REPORT_SAVE_DF(path = path)
        #self.REPORT_SAVE_VIZ_PNG(path = path)
        self.REPORT_SAVE_VIZ_HTML(path = path)
        return self
    
    #def REPORT_SAVE_VIZ_PNG(self, path = None):
    #    'Save all figures into separate png files'
    #    path = self._pathHelper(path, filename='figure')
    #    for i, fig in enumerate(self._figs):
    #        fig.write_image(path+'%d.png' % i, width=1040, height=360, scale=10) 
    #    return self
    
    def REPORT_SAVE_VIZ_HTML(self, path = None, write_type = 'w'):
        'Save all figures into a single html file'
        import datetime
        #path = path if path == Null else path.encode().decode('unicode-escape')
        
        if path in self._config.sections() and 'html' in self._config[path]:
            path = self._config[path]['html']
        else:
            path = self._pathHelper(path, filename='html_report.html')
        with open(path, write_type) as f:
            f.write("Report generated: " + str(datetime.datetime.today()))
            for i, fig in enumerate(self._figs):
                f.write(fig.to_html(full_html=False, include_plotlyjs='cdn', default_height=360, default_width='95%', config=self._fig_config))
            #f.write(self._df.describe(include='all').fillna(value='').T.to_html())
        return self
    
    #def REPORT_SAVE_VIZ_HTML_APPEND(self, path = None):
    #    'Save all figures into a single html file'
    #    return self.REPORT_SAVE_VIZ_HTML(path=path, write_type='a')
    
    def REPORT_SAVE_DF(self, path = None):
        if path in self._config.sections() and 'csv' in self._config[path]:
            path = self._config[path]['csv']
        else:
            #path = path if path == Null else path.encode().decode('unicode-escape')
            path = self._pathHelper(path, filename='dataframe.csv') #pandas needs file extension
        self._df.to_csv(path, index=False)
        return self
    
    def REPORT_SAVE_DF_KINTONE_SYNCH(self, config_section):
        if source in self._config.sections():
            domain = self._config.get(source,'kintone_domain')
            app_id = self._config.getint(source,'app_id')
            api_token = self._config.get(source,'api_token')
            model_csv = self._config.get(source,'model_csv')
            
            m = jsModelFactory.get(model_csv)
            js = JinSapo(domain=domain, app_id=app_id, api_token=api_token, model=m)
            data = jsDataLoader(m, self._df)
            js.synch(data.models())
        else:
            print('Config section not in config.ini: ' + config_section)
        return self
    
    def REPORT_SAVE_DF_KINTONE_ADD(self, config_section):
        if source in self._config.sections():
            domain = self._config.get(source,'kintone_domain')
            app_id = self._config.getint(source,'app_id')
            api_token = self._config.get(source,'api_token')
            model_csv = self._config.get(source,'model_csv')
            
            m = jsModelFactory.get(model_csv)
            js = JinSapo(domain=domain, app_id=app_id, api_token=api_token, model=m)
            data = jsDataLoader(m, self._df)
            js.create(data.models())
        else:
            print('Config section not in config.ini: ' + config_section)
        return self
    
    def REPORT_DASH(self):
        from jupyter_dash import JupyterDash
        import dash_core_components as dcc
        import dash_html_components as html
        from dash.dependencies import Input, Output

        # Load Data
        df = px.data.tips()
        # Build App
        app = JupyterDash(__name__)
        app.layout = html.Div([
            html.H1("JupyterDash Demo"),
            dcc.Graph(id='graph'),
            html.Label([
                "colorscale",
                dcc.Dropdown(
                    id='colorscale-dropdown', clearable=False,
                    value='plasma', options=[
                        {'label': c, 'value': c}
                        for c in px.colors.named_colorscales()
                    ])
            ]),
        ])
        # Define callback to update graph
        @app.callback(
            Output('graph', 'figure'),
            [Input("colorscale-dropdown", "value")]
        )
        def update_figure(colorscale):
            return px.scatter(
                df, x="total_bill", y="tip", color="size",
                color_continuous_scale=colorscale,
                render_mode="webgl", title="Tips"
            )
        # Run app and display result inline in the notebook
        app.run_server(mode='jupyterlab')

    

# ## UTILITIES ###

    def _removeElementsFromList(self, l1, l2):
        '''Remove from list1 any elements also in list2'''
        # if not list type ie string then covert
        if not isinstance(l1, list):
            list1 = []
            list1.append(l1)
            l1 = list1
        if not isinstance(l2, list):
            list2 = []
            list2.append(l2)
            l2 = list2
        #return list(set(l1) - set(l2)) + list(set(l2) - set(l1))
        return [i for i in l1 if i not in l2]
    
    def _commonElementsInList(self, l1, l2):
        if l1 is None or l2 is None: return None
        if not isinstance(l1, list): l1 = [l1]
        if not isinstance(l2, list): l2 = [l2]
        #a_set = set(l1)
        #b_set = set(l2)
        
        # check length
        #if len(a_set.intersection(b_set)) > 0:
        #    return list(a_set.intersection(b_set)) 
        #else:
        #    return None
        return [i for i in l1 if i in l2]
    
    def _colHelper(self, columns = None, max = None, type = None, colsOnNone = True, data_frame=None):
        
        if data_frame is None: data_frame = self._df
        
        # pre-process: translate to column names
        if isinstance(columns, slice) or isinstance(columns, int):
            columns = data_frame.columns.values.tolist()[columns]
        elif isinstance(columns, list) and all(isinstance(c, int) for c in columns):
            columns = data_frame.columns[columns].values.tolist()
        
        # process: limit possible columns by type (number, object, datetime)
        df = data_frame.select_dtypes(include=type) if type is not None else data_frame
        
        #process: fit to limited column scope
        if colsOnNone == True and columns is None: columns = df.columns.values.tolist()
        elif columns is None: return None
        else: columns = self._commonElementsInList(columns, df.columns.values.tolist())           
        
        # apply 'max' check    
        if isinstance(columns, list) and max != None: 
            if max == 1: columns = columns[0]
            else: columns = columns[:max]
        
        return columns
    
    def _rowHelper(self, df, max = None, head = True):
        if max == None: return df
        else: 
            if head == True: return df.head(max)
            else: return df.tail(max)
    
    def _toUniqueColName(self, name, data_frame=None):
        if data_frame is None: data_frame = self._df
        n = 1
        while name in data_frame.columns.values.tolist():
            name = name + str(n)
        return name
    
    def _pathHelper(self, path, filename):
        import os
        if path == None:
            from pathlib import Path
            home = str(Path.home())
            path = os.path.join(home, 'report')
        else:
            path = os.path.join(path, 'report')
        os.makedirs(path, exist_ok = True)
        path = os.path.join(path, filename)
        return path

    
