"""Query node (retrieve + generate).

PURPOSE
    The read path. At query time, call Engineer B's retriever, then run the QA
    chain to generate a grounded answer.

WHAT TO BUILD HERE
    - A node function that takes a QueryRequest and returns a QueryResult.
    - Call the retriever (Contract 2), then chains/qa.py for generation.
    - Assemble sources + latency + tokens into the result.
"""
