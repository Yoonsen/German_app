import os
import streamlit as st

import sqlite3
import pandas as pd
from dhlab.api.dhlab_api import totals
from collections import Counter
import socket


@st.cache_data()
def countby(corpus=None, counts=None, column=None):
    """Deduplicated corpus against a counts object
    :param dedup: is deduplicated corpus
    :param counts: an instance of Counts().counts - i.e the dataframe
    :param column: the column to aggregate over"""
    
    cols = list(counts.columns)
    result = pd.merge(
        dedup[['urn', column]], 
        counts.transpose().reset_index(), 
        left_on='urn', 
        right_on='urn').groupby(column).sum(cols)
    return result


zotero_excel = "POLNET_from1988_load091220c.xlsx"

if not 'zotero' in st.session_state:
    st.session_state['zotero'] = pd.read_excel(zotero_excel)

zotero = st.session_state['zotero']
    


# #  #   #     #     #      C O D E       #      #     #    #   #  # # ###



col1, col2, col3 = st.columns(3)

with col1:
    column = st.selectbox("Velg grupperingskolonne", list(zotero.columns)[1:])

with col2:
    vis = st.selectbox("Vis som", ['dataramme', 'søylediagram', 'linjediagram', 'arealdiagram'])

with col3:
    groups = zotero.groupby(column).count()[['Key']]

try:
    st.write(f"Det er {len(groups)} forskjellige verdier av \'{column}\' i {int(groups.sum())} publikasjoner")
except:
    st.write(f"Størrelse på \'{column}\' lot seg ikke beregne")
    
if vis == 'dataramme':
    st.write(groups)
elif vis == 'søylediagram':
    st.bar_chart(groups)
elif vis == 'linjediagram':
    st.line_chart(groups)
elif vis == 'arealdiagram':
    st.area_chart(groups)
else:
    pass
    