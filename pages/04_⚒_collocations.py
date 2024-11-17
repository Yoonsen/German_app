import os
import streamlit as st

import sqlite3
import pandas as pd
from dhlab.api.dhlab_api import totals
from collections import Counter
import socket

from dhlab.constants import BASE_URL
import requests
import json

st.set_page_config(page_title="Collocations", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

@st.cache_data(show_spinner=False)
def dhlabid_collocation(
        dhlabids = None,
        word = "arbeid",
        before = 5,
        after = 0,
        samplesize = 200000,
):
    """Create a collocation from a list of URNs.

    Call the API :py:obj:`~dhlab.constants.BASE_URL` endpoint
    `/urncolldist_urn`.

    :param list dhlabids: List of identifiers for dhlabid
    :param str word: word to construct collocation with.
    :param int before: number of words preceding the given ``word``.
    :param int after: number of words following the given ``word``.
    :param int samplesize: total number of ``urns`` to search through.
    :return: a ``pandas.DataFrame`` with distance (sum of distances and bayesian distance) and
        frequency for words collocated with ``word``.
    """

    params = {
        "dhlabid": dhlabids,
        "word": word,
        "before": before,
        "after": after,
        "samplesize": samplesize,
    }
    r = requests.post(BASE_URL + "/urncolldist_urn", json=params)
    return json.loads(r.json())


@st.cache_data()
def nbtotals(n = 250000):
    tot = totals(n)
    tot.columns = ['tot']
    tot.tot = tot.tot/tot.tot.sum()
    return tot



st.session_state.update(st.session_state)

corpus = st.session_state['korpus']

############# STREAMLIT CODE CALLBACK ########################

st.session_state.update(st.session_state)

########################## C O D E ##############################################

if "totals" not in st.session_state:
    st.session_state['totals'] = nbtotals()


col1, col2, colbefore, colafter = st.columns(4)
with col1:
    koll_ord = st.text_input("kollokasjon for", st.session_state.get('coll_word', ""), key='coll_word')
    
with col2:
    antall = st.number_input("maks antall treff",
                             min_value = 1, 
                             max_value = 5000, 
                             value = st.session_state.get('size', 200), 
                             key='size')
with colbefore:
    kontekst_before = st.number_input('antall ord før', min_value = 0, max_value = 50, value = st.session_state.get('window', 10), key="window")
with colafter:
    kontekst_after = st.number_input('antall ord etter', min_value = 0, max_value = 50, value = st.session_state.get('after', 10), key="after")
    

colls = pd.DataFrame(dhlabid_collocation(st.session_state.dhlabid,  koll_ord, before = kontekst_before, after = kontekst_after, samplesize = antall))


collrel = colls['counts']/colls['counts'].sum()
#st.write(collrel.head(10))
colls['relevance'] = collrel/st.session_state.totals.tot


st.session_state["colls"] = colls


# Display the dataframe


st.dataframe(st.session_state["colls"].sort_values(by='relevance', ascending=False), hide_index=False)
