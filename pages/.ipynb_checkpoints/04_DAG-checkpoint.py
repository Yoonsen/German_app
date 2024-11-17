import os
import streamlit as st

from collections import Counter
import math

import sqlite3
import pandas as pd
from dhlab.api.dhlab_api import totals
from collections import Counter
import socket

import re
import networkx as nx


import matplotlib.pyplot as plt

def file_selector(folder_path='.'):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox('Select a file', filenames)
    return os.path.join(folder_path, selected_filename)



def query(db, query, params = ()):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        res = cur.execute(query, params)
    return res.fetchall()


st.set_page_config(page_title="POLNET GRAF", page_icon=None, layout="wide")

#zotero_excel = "POLNET_from1988_load091220c.xlsx"

if not 'zotero' in st.session_state:
    st.write("gå til korpus-siden for å initialisere zotero-korpus")
    #st.session_state['zotero'] = pd.read_excel(zotero_excel)

zotero = st.session_state['zotero']
    
# In[131]:


#zotero = pd.read_excel(zotero_excel, engine='openpyxl').fillna('')

# In[98]:





############# STREAMLIT CODE CALLBACK ########################

#st.session_state.update(st.session_state)

########################## C O D E ##############################################

@st.cache_data()
def make_ref_graph(z):

    referanser = list(z[['Key','Notes']].to_records())
    #print(referanser[:3])
    reference_dict = {
        referanser[i][1]:re.findall("<p>([0-9A-Z]+)</p>", referanser[i][2]) 
        for i in range(len(referanser)) 
        if  type(referanser[i][2]) is str
    }
    #print(reference_dict)
    
    edge_list = [(y, x) for x in reference_dict for y in reference_dict[x] if y != x]
    edge_list = [(a, b) for (a, b) in edge_list if (b, a) not in edge_list]
    
    def label_from_z(e):
        try:
            res = z[z.Key==e]['Title'].values[0]
            elements = res.split()
            if elements[0] == "NOU":
                res = ' '.join(elements[:3])
            elif elements[0].startswith('St'):
                res = ' '.join(elements[:4])
            else:
                res = 'unknown'
        except:
            res = 'unknown'
        return str(res)
    
    
    nodelist = [(e, {'name':label_from_z(e)}) for e in z.Key.values ] 
    

    G = nx.DiGraph()
    
    G.add_edges_from(edge_list)
    G.add_nodes_from(nodelist)
    
    # add name for root element
    #G.nodes[0]['name'] = 'root'
   
    return G

def make_label(l, n):
    w = l.split()
    return ' '.join(w[:n])

def draw_graph(G, str_size=3):
    #edgelabels = {(x[0], x[1]):x[2]['name'] for x in G.edges(data=True)}
    nodelabels = {x[0]:x[1].get('name', x[0]) for x in G.nodes(data=True)}
    labelcolors = {x:'green' if nodelabels[x].startswith("NO") else 'pink' for x in nodelabels}
    pos =  nx.nx_agraph.graphviz_layout(G, prog = "dot")
    G.graph.setdefault('graph', {})['rankdir'] = 'TB'
   
    n = nx.dag_longest_path(G)
    #st.write(n)
    fig = plt.figure(figsize=(30,1.4*len(n)))
    
    
    options = {"edgecolors": "tab:gray", "node_size": 0, "alpha": 0.5, "nodesep":0.75, "rank":"source"}
    nx.draw_networkx_edges(G, pos, width=1.2, alpha=0.1, arrows=True, edge_color='gray', connectionstyle="arc3,rad=0.3");
    #nx.draw_networkx_edge_labels(G, pos, edge_labels = edgelabels, font_size=8,font_color='orange');
    
    main_nodes = [n[0] for n in Counter(nx.degree_centrality(G)).most_common()]
    
    m = len(main_nodes)
    d = int(math.log(m, 2))
    j = 0
    splices = []
    for i in range(2, d+2, 3):
        k = 2**i
        splices.append(main_nodes[j:k])
        j = k
    splices.append(main_nodes[j:])
    for f,subgr in enumerate(splices): 
        factor = 1/(1.2*f + 1)
        greens = [n for n in subgr if labelcolors[n] == 'green']
        pinks = [n for n in subgr if labelcolors[n] == 'pink']
        
        nx.draw_networkx(G.subgraph(greens), 
                         pos=pos, labels = {x:nodelabels[x] for x in G.subgraph(greens).nodes()}, 
                         node_color = 'green', font_color="black", alpha=factor, font_size=12);
        
        nx.draw_networkx(G.subgraph(pinks), 
                         pos=pos, 
                         labels = {x:nodelabels[x] for x in G.subgraph(pinks).nodes()}, 
                         node_color = 'pink',  font_color="black", alpha=factor,
                         font_size=12);
    st.pyplot(fig)

st.write("#### Inspiser graf")

with st.form('Graf basert på delkorpus'):
    
    col1, col2, col3 = st.columns(3)

    with col1:
        column = st.selectbox("Lag et subcorpus basert på verdier i ", list(zotero.columns)[1:])

    with col2:
        value = st.text_input("Verdier ", "", help="la verdien stå tom for å velge hele korpuset")

    with col3:
        sammenlign = st.selectbox("Sammenligning", [ 'delstreng', 'mindre enn (eller lik)', 'større enn (eller lik)', 'likhet'])
    
    

    if st.form_submit_button("Visualiser DAG"):  
        subset = zotero
        if value != "":
            if sammenlign == 'delstreng':
                subset = zotero[zotero[column].fillna('').str.contains(value)]
            elif sammenlign == 'likhet':
                subset = zotero[zotero[column] == value]
            elif sammenlign.startswith('mindre'):
                subset = zotero[zotero[column] <= int(value)]
            elif sammenlign.startswith('større'):
                subset = zotero[zotero[column] >= int(value)]

        G = make_ref_graph(subset)
        if len(G) > 0:
            try:
                draw_graph(G)
            except:
                st.write(nx.find_cycle(G, source=None, orientation=None))
        else:
            st.write("Tom graf")