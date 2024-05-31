import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import re

import ollama
from langchain_community.llms import Ollama

indexName = "hkdata1"

def get_es_connection():
    try:
        es = Elasticsearch("http://localhost:9200/")
        if es.ping():
            st.session_state.es = es
            print('successfully connected to es')
        else:
            print("Oops! Cannot connect to Elasticsearch!")
    except ConnectionError as e:
        print(f"Connection Error: {e}")

# Ensure Elasticsearch connection is stored in session state
if 'es' not in st.session_state:
    get_es_connection()

# Example usage of the Elasticsearch connection
if 'es' in st.session_state:
    es = st.session_state.es
    # Example operation using the ES connection
    try:
        info = es.info()
        
    except Exception as e:
        st.error(f"Error fetching Elasticsearch info: {e}")


def removekaro(input_string):
    return input_string.replace(",", "")

def parse_search_results(input_string: str,results) -> list:
    # print(results)
    colon_index = input_string.rfind(":")

    if colon_index != -1:
        names_string = input_string[colon_index + 1:]
    else:
        names_string = input_string

    names = [name.strip() for name in names_string.split(",")]

    results_list = names[:20]
    
    res = []

    for result in results_list:
        res.append(results[result])

    return res

def context_search(input_keyword):
    
    model = SentenceTransformer('all-mpnet-base-v2')
    vector_of_input_keyword = model.encode(input_keyword)

    
    query = {
            "field": "embeddings",
            "query_vector": vector_of_input_keyword,
            "k": 100,
            "num_candidates": 1000
        }
    res = es.knn_search(index="hkdata1"
                            , knn=query 
                            , source=["fullName","search_text","br_nm","secondary_category","_id"]
                            )
    results = res["hits"]["hits"]

    data_for_llama3 = {}
    appended_string = ""

    for hit in results:
        full_name = removekaro(hit["_source"]["fullName"])
        full_name = full_name.strip()
        data_for_llama3[str(hit["_id"])] = hit
        appended_string += full_name + " " + hit["_id"] + ", " 

    appended_string = appended_string[:-2]  

    llama3_prompt = f"Select the 20 best options from the given options to the question '{input_keyword}':\n{appended_string} just give out the ID which is mentioned just before a comma give them out in a single separated by commas"
    # print(llama3_prompt)
    llm = Ollama(model="llama3")
    res = llm.invoke(llama3_prompt)
    # print(res)
    ans = parse_search_results(res,data_for_llama3)
    # print(ans)
    return ans


def printres(data):
    st.subheader("Search Results")
    for result in data:
                with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        st.divider()

def search(input_keyword, page):

    query = {
        "query": {
            "multi_match": {
                "query": input_keyword,
                "fields": ["fullName", "search_text", "br_nm"],
                "fuzziness": 2
            }
        },
        "from": page * 10,  
        "size": 10  
    }
    
    res = es.search(index="hkdata1", body=query)
    results = res["hits"]["hits"]
    print("ran query with page no " + str(page))
    return results

def search_count(input_keyword):

    query = {
        "query": {
            "multi_match": {
                "query": input_keyword,
                "fields": ["fullName", "search_text", "br_nm"],
                "fuzziness": 2
            }
        },
        
        "size": 40
    }
    
    res = es.search(index="hkdata1", body=query)
    results = res["hits"]["hits"]
    return results

def main():
    st.title("Search at HealthKart")

    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    search_query = st.text_input("Enter your search query", value=st.session_state.search_query)
    
    if st.button("Search"):
        st.session_state.search_query = search_query
        st.session_state.page_number = 0  
        st.session_state.total = len(search_count(st.session_state.search_query))
        st.session_state.search_results = context_search(search_query)
    if st.session_state.search_query:
        
        N = 10
        
        last_page =  2+(st.session_state.total//N) 
        
        prev, _ ,next = st.columns([5, 10, 5])

        if st.session_state.page_number < last_page :
            if next.button("Next"):
                st.session_state.page_number += 1

        if st.session_state.page_number > 0 :
            if prev.button("Previous"):          
                st.session_state.page_number -= 1

        if st.session_state.page_number > last_page -3:
            
            if st.session_state.page_number == last_page -2:
                printres(st.session_state.search_results[:10])
            else : printres(st.session_state.search_results[10:])

        
        else :
            results = search(st.session_state.search_query,st.session_state.page_number)
            data = results
            printres(data)
                    
if __name__ == "__main__":
    main()


