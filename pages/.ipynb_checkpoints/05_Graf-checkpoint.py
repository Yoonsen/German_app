import os
import streamlit as st

from collections import Counter
import math

import sqlite3
import pandas as pd
from dhlab.api.dhlab_api import totals
import dhlab.graph_networkx_louvain as gnl 
from collections import Counter
import socket

import re
import networkx as nx
from streamlit_agraph import agraph, TripleStore, Config, Node, Edge

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
    pass
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
    
    nodelist = [(e, {'name':label_from_z(e)}) for e in z.Key.values] 
    ns = [x[0] for x in nodelist]
    edge_list = [(y, x) for x in reference_dict for y in reference_dict[x]]
    #edge_list = [(a, b) for (a, b) in edge_list if (b, a) not in edge_list]

    G = nx.Graph()
    
    G.add_nodes_from(nodelist)
    G.add_edges_from(edge_list)
   
    attrs = {x[0]: {"name": x[0]} for x in G.nodes(data=True) if x[1] == {}}
    nx.set_node_attributes(G, attrs)
            
        
    # add name for root element
    #G.nodes[0]['name'] = 'root'
    #st.write(G.nodes(data = True))
    #st.write(ns, G.edges())
    return G

def make_label(l, n):
    w = l.split()
    return ' '.join(w[:n])

colors =  ['#DC143C','#FFA500',
           '#F0E68C','#BC8F8F','#32CD32',
           '#D2691E','#3CB371','#00CED1',
           '#00BFFF','#8B008B','#FFC0CB',
           '#FF00FF','#FAEBD7']

def word_to_colors(comm):
    word_to_color = dict()
    for i, e in enumerate(comm.values()):
        for x in e:
            word_to_color[x] = colors[i % len(colors)]
    return word_to_color

ERRORS = []

def create_nodes_and_edges_config(g, community_dict):
    """create nodes and edges from a networkx graph for streamlit agraph, classes Nodes, Edges and Config must be imported"""
    cmap = word_to_colors(community_dict)
    nodes = []
    edges = []
    cent = nx.degree_centrality(g)
    for i in g.nodes(data = True):
        #st.write(i)
        try:
            nodes.append(Node(id=i[0], label=i[1]['name'], size=100*cent[i[0]], color=cmap[i[0]]) )
        except:
            ERRORS.append(i)
    for i in g.edges(data = True):
        edges.append(Edge(source=i[0], target=i[1], color = "#ADD8E6"))

    config = Config(
        width=1500, height=1000,
        directed=True, 
    )
    
    return nodes, edges, config

def graf_data(word, lang='nob', corpus = 'all', cutoff = 16):
    if lang == 'nob':
        res = word_graph(word, corpus = corpus, cutoff = cutoff)
    else:
        res = nb.make_graph(word, lang = lang, cutoff = cutoff)
   
    comm = gnl.community_dict(res)
    cliques = gnl.kcliques(res.to_undirected())
    return res, comm, cliques

    


st.write("#### Inspiser graf")

with st.form('Graf basert på delkorpus'):
    
    col1, col2, col3 = st.columns(3)

    with col1:
        column = st.selectbox("Lag et subcorpus basert på verdier i ", list(zotero.columns)[1:])

    with col2:
        value = st.text_input("Verdier ", "", help="la verdien stå tom for å velge hele korpuset")

    with col3:
        sammenlign = st.selectbox("Sammenligning", ['delstreng', 'mindre enn (eller lik)', 'større enn (eller lik)', 'likhet'])
    
    

    if st.form_submit_button("Visualiser graf som uretted graf - force layout"):  
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
            fig, ax = plt.subplots()
            if nx.is_empty(G):
                st.write(" -- ingen treff --")
            else:
                nodes, edges, config = create_nodes_and_edges_config(
                    G, 
                    gnl.community_dict(G)
                )
                agraph(nodes, edges, config)
        else:
            st.write("Tom graf")