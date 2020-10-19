# %%
import json
import pandas as pd
import itertools
import ast
from pandas.io.json import json_normalize 
import os
import ast
import numpy as np
import gzip
import shutil

def Read_Cookies(filenames,stop_max=False):
    looperino = 1
    with open(filenames,"r",encoding="UTF-8", errors="ignore") as in_file:
        dicts = []
        for line in in_file.readlines(): 
            d = json.loads(line.strip())
            dicts += [d]
            looperino = looperino +1
            if (looperino > 2500) and (stop_max == True):
                break
    return(dicts)

#Get mappiings
def get_dictionary_mappings():
    with open('mappings.json',"r",encoding="UTF-8",errors = 'ignore')as infile:
        mappings = []
        for line in infile.readlines(): 
            d = json.loads(line.strip())
            mappings += [d]
    mappper=[]
    for map in mappings:
        beh_id = map['behavior_id']
        hierarchy_nodes = map['hierarchy_nodes']
        for hierarchy in hierarchy_nodes:
            mappper.append((beh_id,hierarchy['id'],hierarchy['path']))

    df = pd.DataFrame(mappper, columns=['beh_id','tax_id',"path_id"])
    diccionario_relevante = df[["beh_id","tax_id"]]
    diccionario_relevante = diccionario_relevante.astype(int)
    diccionario_relevante = diccionario_relevante.astype(str)
    # diccionario_relevante = diccionario_relevante.select_dtypes(include='str')
    diccionario_relevante_dict = diccionario_relevante.set_index('beh_id').to_dict()['tax_id']
    return(diccionario_relevante_dict)

diccionario_relevante_dict = get_dictionary_mappings()

def replace_id_beh_for_taxonomy_node():
    working_df = pd.read_csv("WeightedEdgelist.csv")
    working_df = working_df.loc[:,~working_df.columns.str.contains('^Unnamed')]
    working_df = working_df.astype(int)
    working_df = working_df.astype(str)
    # work = working_df.select_dtypes(include='str')
    i=0
    fails = pd.DataFrame()
    table = pd.DataFrame()
    for chunk in np.array_split(working_df, 250):
        print(i)
        try:
            chunkerino = chunk.replace({'To':diccionario_relevante_dict})
            chunkerino = chunkerino.replace({'From':diccionario_relevante_dict})
            table = pd.concat([table,chunkerino])
        except TypeError as identifier:
            print("failed at",i)
            fails = pd.concat([fails,chunk])
            pass
            i = i+1
    table = table[table['To'] != table['From']]
    # table = table.to_csv('replacededgelist_aux.csv')
    return table

def reduce_total_taxonomy_edgelist_to_category_shopping_taxonomy(table,diccionario_relevante_dict):
    reducido = pd.read_csv("FolderAsesorSinodal/node_level_data_Shorthand_Reducido.csv").dropna()
    tablenew = table.loc[table['To'].isin(list(reducido['Node_ID']))]
    tablenew = tablenew.loc[table['From'].isin(list(reducido['Node_ID']))]
    diccionario_relevante = reducido[["Node_ID","NEWID"]]
    diccionario_relevante = diccionario_relevante.astype(int)
    diccionario_relevante = diccionario_relevante.astype(str)
    # diccionario_relevante = diccionario_relevante.select_dtypes(include='str')
    diccionario_relevante_dict = diccionario_relevante.set_index('Node_ID').to_dict()['NEWID']
    final_table = tablenew.replace({'To':diccionario_relevante_dict})
    final_table = final_table.replace({'From':diccionario_relevante_dict}).groupby(["To","From"]).sum().reset_index()
    final_table = final_table.loc[:,~final_table.columns.str.contains('^Unnamed')]
    final_table.to_csv("WeightedExpandedReplacedEdgelist.csv",index=False)
    return(final_table)


def get_file_type(filepath,typerino):
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*'+typerino))
        for f in files :
            all_files.append(os.path.abspath(f))
    return all_files


def CreateHierarchyEdgelist_optim(dicts,filename):
    # import ast
    iter = 0
    Listed = []
    Listed2 = []
    ListOfLists = []
    ListOfLists2 = []
    TimeStampList = []
    InnerIter = 1
    for record in dicts:
        events = record['events'][0]
        if 'add' in events.keys():
            TimeStamp = events['ts']
            EventList = events['add']
        else:
            TimeStamp = events['ts']
            EventList = events['remove']
        Listed = []
        Listed2 = []
        for happen in EventList:
            DataF = Taxonomy[Taxonomy['behavior_id'] == happen]
            if DataF.empty:
                NADA = "Nada"
            else:
                for i in range(len(DataF)):
                    Hier = Taxonomy[Taxonomy['behavior_id'] == happen].reset_index()['behavior_id'][i]
                    Hier = str(Hier)
                    Listed.append(Hier)
        ListOfLists.append(list(pd.Series(Listed, name='A').unique()))
        ListOfLists2.append(Listed2)
        TimeStampList.append(TimeStamp)
        iter = iter + 1
        if iter % 50 ==0: 
            a = ListOfLists
            a2 = ListOfLists2
            Edges = []
            EdgesTax = []
            TimeAuxList = []
            for i in range(len(ListOfLists)):
                if len(ListOfLists[i]) > 50:
                    ListOfLists[i] = ListOfLists[i][0:50]
                h = itertools.combinations(ListOfLists[i], 2)
                TimeAux = TimeStampList[i]
                for comb in h:
                    Edges.append(comb)
                    TimeAuxList.append(TimeAux)
            for lists in a2:
                if len(lists) > 50:
                    lists = lists[0:50]
                h2 = itertools.combinations(lists,2)
            Edges = pd.DataFrame(Edges, columns = ["To","From"])
            TimeAuxList = pd.DataFrame(TimeAuxList, columns= ['TimeStamp'])
            Edges = pd.concat([Edges.reset_index(drop=True),TimeAuxList],axis=1)
            Edges.to_csv(str(filename)+ "_" +str(InnerIter)+".csv")
            InnerIter = InnerIter + 1
            print(InnerIter*50/len(dicts),"percentage of task done")
        if iter % 50 ==0:
            Listed = []
            Listed2 = []
            ListOfLists = []
            ListOfLists2 = []
            TimeStampList = []
        if iter % len(dicts) == 0:
            a = ListOfLists
            a2 = ListOfLists2
            Edges = []
            EdgesTax = []
            TimeAuxList = []
            for i in range(len(ListOfLists)):
                if len(ListOfLists[i]) > 50:
                    ListOfLists[i] = ListOfLists[i][0:50]
                h = itertools.combinations(ListOfLists[i], 2)
                TimeAux = TimeStampList[i]
                for comb in h:
                    Edges.append(comb)
                    TimeAuxList.append(TimeAux)
            for lists in a2:
                if len(lists) > 50:
                    lists = lists[0:50]
                h2 = itertools.combinations(lists,2)
            Edges = pd.DataFrame(Edges, columns = ["To","From"])
            TimeAuxList = pd.DataFrame(TimeAuxList, columns= ['TimeStamp'])
            Edges = pd.concat([Edges.reset_index(drop=True),TimeAuxList],axis=1)
            Edges.to_csv(str(filename)+ "_" +str(InnerIter)+".csv")
            Inneriter = InnerIter + 1
            print(InnerIter*50/len(dicts),"percentage of task done")
            print("Finished")

def master_sampler():
    GZIPdirectory = 'E:/Data & Thesis/DataStreamZIPDUMP'
    gzips_location = get_file_type(GZIPdirectory,'.gz')
    list_of_stop_words = ["Edges", "Florentine", "mappings.json.gz","TaxonomyMain.csv"]
    filtered_str = [x for x in gzips_location if x not in set(list_of_stop_words)]
    i = 1
    weighted_edge_list = pd.DataFrame()
    weighted_edge_list.to_csv("WeightedEdgelist.csv")
    donefiles = []
    try:
        os.mkdir('Auxfiles') 
    except OSError as e:
        print("Ya esta el directorio")
    for file in filtered_str:
        fp = open("zen1.txt", "wb")
        with gzip.open(file,'rb') as f:
            data = f.read()
        fp.write(data)
        fp.close()
        dicts = Read_Cookies("zen1.txt")
        CreateHierarchyEdgelist_optim(dicts,"Auxfiles/aux")
        j = 0
        aux_files = get_file_type("Auxfiles",'.csv')
        weighted_edge_list = pd.read_csv("WeightedEdgelist.csv")
        weighted_edge_list = weighted_edge_list.loc[:,~weighted_edge_list.columns.str.contains('^Unnamed')]
        for auxs in aux_files:
            Thing = pd.read_csv(auxs)
            if len(Thing)>0:
                max_batch = max(Thing['TimeStamp'])
                min_batch = min(Thing['TimeStamp'])
                Thing = Thing[['To','From']]
                Thing['freq']=Thing.groupby(by=['To'])[['To']].transform('count')
                Thing = Thing[Thing['To'] != Thing['From']]
                weighted_edge_list = pd.concat([Thing,weighted_edge_list]).groupby(["To","From"]).sum().reset_index()
                j = j +1
                print(j/len(aux_files),"Appending done")
        try:
            shutil.rmtree('Auxfiles')
        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))
        try:
            os.mkdir('Auxfiles') 
        except OSError as e:
            print("Ya esta el directorio")
            pass
        print(i*100/len(filtered_str),"PERCENTAGE OF GZ FILES DONE")
        donefiles.append(file)
        i = i+1
    fp = open("gzips.txt", "wb")
    fp.write(donefiles)
    fp.close()
    return(donefiles)
# %%
def check_time_logs():
    with open('gzips.txt',"r",encoding="utf-8", errors="ignore") as in_file:
            dicts = []
            for line in in_file.readlines():
                line = line.replace('\\','/')
                line = line.replace('\n','')
                dicts += [line]
    min_time = 1536486306
    max_time = 1536486306 #First observation of the cookies
    cookies = 0
    iter2 = 0
    total = 0
    for file in dicts:
        size = os.path.getsize(file)
        total = total + size
    for file in dicts:
        fp = open("zen1.txt", "wb")
        with gzip.open(file,'rb') as f:
            data = f.read()
            fp.write(data)
            fp.close()
        dictss = Read_Cookies("zen1.txt")
        for dicty in dictss:
            time = dicty['events'][0]['ts']
            if time < min_time:
                min_time=time
            if time > max_time:
                max_time = time
        print(min_time,max_time)
        iter2 = iter2 +1
        cookies = cookies + len(dictss)
        print(iter2/len(dicts))
    #max_time de la muestra es: 1537286399
    #min_time de la muestra es: 1536267600
    #numero de registros de cookies: 25435675
    return(max_time,min_time,total)

# %%

