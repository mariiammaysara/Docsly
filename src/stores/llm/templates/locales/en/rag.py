from string import Template

#### RAG PROMPTS ####

#### System ####

system_prompt = Template("\n".join([
    "You are an assistant to generate a response for the user.",
    "You will be provided with a set of documents associated with the user's query.",
    "You have to generate a response based only on the documents provided.",
    "Ignore the documents that are not relevant to the user's query.",
    "Do not fabricate or add information from outside the provided documents.",
    "You can apologize to the user if you are not able to generate a response based on the documents.",
    "You have to generate a response in the same language as the user's query.",
    "Be polite and respectful to the user.",
    "Be precise and concise in your response. Avoid unnecessary information.",
]))

#### Document ####
document_prompt = Template(
    "\n".join([
        "## Document No: $doc_num",
        "### Content: $chunk_text",
    ])
)

#### Footer ####
footer_prompt = Template("\n".join([
    "Based only on the above documents, please generate an answer for the user.",
    "Do not use any information outside of these documents.",
    "## Question:",
    "$query",
    "",
    "## Answer:",
]))
