from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import streamlit as st
from langchain_community.llms import Ollama


  
try:
  es = Elasticsearch(['http://localhost:9200'])
  print("Successfully connected to Elasticsearch.")
  
except Exception as e:
  print(f"Failed to connect to Elasticsearch: {e}")


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


# context_search("keto diet")

def printres(results,brand,category,myset):
    count = 0
    if brand and category:
        for result in results:
            
            if count == 21 : break
            if( result['_source']['secondary_category'].lower()!=category.lower().strip() or result['_source']['br_nm'].lower()!=brand.lower().strip()): continue
            count += 1
            myset.add(result['_source']['fullName'])
            with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: I am a result of filtering both brand and category")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
    if brand:
        for result in results:
            if count == 21 : break
            if(result['_source']['br_nm'].lower()!=brand.lower().strip()): continue
            
            if result['_source']['fullName'] not in myset:
                with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: I am a result of filtering  brand ")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
                myset.add(result['_source']['fullName'])
                count += 1
    if category:
        for result in results:
            if count == 21 : break
            if(result['_source']['secondary_category'].lower()!=category.lower().strip()): continue
            if result['_source']['fullName'] not in myset:
                with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: I am a result of filtering category ")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
                myset.add(result['_source']['fullName'])
                count += 1
    for result in results:
        if count == 21 : break 
        if result['_source']['fullName'] not in myset:
                with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: {result['_source']['search_text']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
                myset.add(result['_source']['fullName'])
                count += 1



def main():
    st.title("Search at HealthKart")

    query = st.text_input("Enter your search query")
    

    if st.button("Search"):

        st.subheader("more Results")
        
        more_results = context_search(query)
        myset = set()
        printres(more_results,None,None,myset)

if __name__ == "__main__":
    main()
