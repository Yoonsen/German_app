import os
import streamlit as st

import sqlite3
import pandas as pd
from dhlab.api.dhlab_api import totals
from collections import Counter
import socket
import dhlab as dh
import requests

st.set_page_config(page_title="Concordance", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

@st.cache_data()
def concordance(
        dhlabids = None, words = None, window = 25, limit = 100
):
    """Get a list of concordances from the National Library's database.

    Call the API :py:obj:`~dhlab.constants.BASE_URL` endpoint
    `/conc <https://api.nb.no/dhlab/#/default/post_conc>`_.

    :param list urns: uniform resource names, for example:
        ``["URN:NBN:no-nb_digibok_2008051404065", "URN:NBN:no-nb_digibok_2010092120011"]``
    :param str words: Word(s) to search for.
        Can be an SQLite fulltext query, an fts5 string search expression.
    :param int window: number of tokens on either side to show in the collocations, between 1-25.
    :param int limit: max. number of concordances per document. Maximum value is 1000.
    :return: a table of concordances
    """
    if words is None:
        return {}  # exit condition
    else:
        #st.write("antall urner:", len(urns))
        params = {"dhlabids": dhlabids, "query": words, "window": window, "limit": limit}
        r = requests.post(dh.constants.BASE_URL + "/conc", json=params)
        if r.status_code == 200:
            res = r.json()
        else:
            res = []
    return pd.DataFrame(res)



st.session_state.update(st.session_state)

st.session_state.update(st.session_state)

col1, col2, col3 = st.columns(3)
with col1:
    konk_ord = st.text_input("konkordans for", st.session_state.get('conc_word', ''), key='conc_word', help="Angi søkeuttrykk med ett eller flere ord som 'lapp', 'lapp*' eller NEAR(lapp kven, 15)")
    
with col2:
    antall = st.number_input("maks antall konkordanser", min_value = 1, max_value = 5000, value = st.session_state.get('conc_numbers', 100), key='conc_numbers')
with col3:
    kontekst = st.number_input('størrelse på konkordanse', min_value = 1, max_value = 100, value = st.session_state.get('conc_window', 10), key = 'conc_window')

if konk_ord != '':
    concs = concordance(st.session_state.dhlabid, words=konk_ord, limit=antall, window=kontekst)[['urn','conc']]
    concs['url'] = concs.urn.apply(lambda x: f"https://nb.no/items/{x}?searchText={konk_ord}")
    concs['Konkordans'] = concs.conc.apply(lambda x: x.replace('<b>','**').replace('</b>', '**'))
    st.write("Antall konkordanser", len(concs))
    st.dataframe(concs[['url','Konkordans']],
        column_config={
            "url": st.column_config.LinkColumn("URL"),
            "Konkordans": st.column_config.TextColumn()
        },
        hide_index=True)