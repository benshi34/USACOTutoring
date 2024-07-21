import streamlit as st
import openai
import json
import time
# import pyperclip

def generate_response(history, api_key, model='gpt-3.5'):
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=history
    )
    return response['choices'][0]['message']['content']

def main():
    st.title("USACO Human Tutoring")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        # Define the options for the multiple choice
        options = ['gpt-3.5-turbo', 'gpt-4o', 'gpt-4-1106-preview', 'gpt-4-turbo', 'choose your own']
        selected_option = st.radio('Select a Model', options, options.index('gpt-4o'))
        if selected_option == 'choose your own':
            model_id = st.text_input("Type in OpenAI model API endpoint")
            st.session_state["openai_model"] = model_id
        else:
            st.session_state["openai_model"] = selected_option

        st.subheader("Formatting Prompt:")
        openai_api_key = st.text_input('OpenAI API Key', type='password')

        file1 = open('usaco_dict.json')
        file2 = open('postcutoff_problems_dict.json')
        usaco_data1 = json.load(file1)
        usaco_data = json.load(file2)
        usaco_data.update(usaco_data1)

        # Question select
        questions = list(usaco_data.keys())
        search_term = st.text_input("Silly search bar:")
        filtered_questions = [question for question in questions if search_term.lower() in question.lower()]
        selected_option = st.selectbox("Select a USACO question: ", filtered_questions, key="unique_key")

        # Question solving prompt:
        description = usaco_data[selected_option]['description']
        problem_link = usaco_data[selected_option]['problem_link']
        problem_link_statement = f"To submit, utilize the problem link below. Make sure to create an account or you won't be able to submit! \n {problem_link}."
        base_prompt = "Please reply with a Python 3 solution to the below problem. Make sure to wrap your code in '```python' and '```' Markdown delimiters, and include exactly one block of code with the entire solution. Feel free to either return just the one code block with your solution or the one code block with explanatory text before and/or after -- however, you will only be evaluated on the correctness of your code.\n\n[BEGIN PROBLEM]\n{}\n[END PROBLEM]\n\n"
        initial_prompt = base_prompt.format(description)
        text_input = st.text_area("Problem Prompt:", value=initial_prompt)
        # if st.button("Copy prompt to Clipboard"):
        #     if text_input:
        #         # Copy the text to the clipboard
        #         pyperclip.copy(initial_prompt)
        #         st.success("Text copied to clipboard!")
        #     else:
        #         st.warning("No text to copy.")
        st.write(problem_link_statement)
    
    if st.button("Reset Conversation"):
        st.session_state.messages = []
    # trajectories = []
    # for filename in os.listdir('trajectories'):
    #     # Join the directory path with the filename to get the full path
    #     full_path = os.path.join('trajectories', filename)
        
    #     # Check if it is a file
    #     if os.path.isfile(full_path):
    #         trajectories.append(filename)
    
    # selected_trajectory = st.selectbox("Select an existing trajectory: ", trajectories)
    query_params = st.experimental_get_query_params()
    if 'trajectory' in query_params and query_params['trajectory']:
        trajectory = query_params['trajectory'][0]
        try:
            file = open('trajectories/'+trajectory+'.json')
            json_data = json.load(file)
            st.session_state.messages = json_data

        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please select a valid JSON file.")  

    uploaded_file = st.file_uploader("Upload Conversation", type=["json"])
    if uploaded_file:
        file_contents = uploaded_file.read()
        print(file_contents)
        try:
            json_data = json.loads(file_contents)
            st.session_state.messages = json_data

        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid JSON file.")
    if st.button("Export Conversation"):
        json_str = json.dumps(st.session_state.messages, indent=2)
        filename = 'message_history.json'
        st.download_button(
            label="Download JSON",
            data=json_str,
            key="json-data",
            on_click=None,
            file_name=filename,
        )
    
    if not 'trajectory' in query_params:
        st.subheader("Instructions:")
        st.write("To begin, first input an OpenAI API key on the left hand side. Then, select a problem from the search bar, and copy + paste the prompt to the model. Alternatively, you may upload an existing JSON conversation, or select one of the preset. To evaluate generated code, paste generated code into a python file, and upload said file to the website provided below the problem statement on the left hand bar. Be aware you must create an account first! Happy tutoring :)")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Copy problem here!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            openai.api_key = openai_api_key
            message_placeholder = st.empty()
            full_response = ""
            for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=st.session_state.messages,
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # if st.session_state.messages and "```python" in st.session_state.messages[-1]['content']:
    #     # Prompt the user for the code results 
    #     code_results = st.text_area("Enter the outcome of the code here:")
    #     if code_results:
    #         with st.chat_message("user"):
    #             st.markdown(code_results)
    #         st.session_state.messages.append({"role": "user", "content": code_results})
    
    if st.button("Regenerate"):
        st.session_state.messages.pop(-1)
        with st.chat_message("assistant"):
            openai.api_key = openai_api_key
            message_placeholder = st.empty()
            full_response = ""
            for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=st.session_state.messages,
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        
if __name__ == '__main__':
    main()