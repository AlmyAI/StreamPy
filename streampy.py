from streampy_console import Console
import logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)
from streamlit_ace import st_ace
from streamlit_deferrer import st_deferrer,st_output,KeyManager
import streamlit as stl
import os

#-------------Initialize session_state variables--------------

state=stl.session_state #shortcut

#Useful to generate unique keys for widgets
if 'key_manager' not in state:
    state.key_manager=KeyManager()
km=state.key_manager

#Main streamlit commands deferrer for the console queue (allows using streamlit commands directly in the input cell)
if 'deferrer' not in state:
    state.deferrer=st_deferrer(key_manager=km)
st=state.deferrer
st.reset()

#the file currently open in the editor
if 'open_file' not in state:
    state.open_file=None

#the content of the file open in the editor
if 'file_content' not in state:
    state.file_content=None

#whether to show the editor or not
if 'show_editor' not in state:
    state.show_editor=False

#Not so useful here, will be removed later
if 'input_deferrer' not in state:
    state.input_deferrer=st_deferrer(key_manager=km)
sti=state.input_deferrer

#The current key of the input cell (changing the key allows to reset the input cell to empty, otherwise the last text typed remains)
if 'input_key' not in state:
    state.input_key = km.gen_key()

#The code displayed in the input cell
if 'input_code' not in state:
    state.input_code = st_output(deferrer=sti,context=None)

#The code outputted by the input cell
if 'output_code' not in state:
    state.output_code = st_output(deferrer=sti,context=None)

#The current key of the editor ace widget
if 'editor_key' not in state:
    state.editor_key = km.gen_key()

#A variable allowing to access the console queue container from anywhere
if 'console_queue' not in state:
    state.console_queue=None

#The current input history index
if 'index' not in state:
    state.index = 0

#------------------------------Main functions-------------------------------------

#Save the content of the editor as... 
def save_as(name):
    with open('./UserFiles/'+name,'w') as f:
        f.write(state.file_content)
    state.open_file=name

#Closes the editor
def close_editor():
    state.show_editor=False
    state.open_file=None
    state.file_content=None

#Runs the code content open in the editor in the console  
def run_editor_content():
    code=state.file_content
    with state.console_queue:
        console.run(code)
    stl.experimental_rerun()

#Opens a new buffer or file in the editor
def edit(file):
    state.show_editor=True
    state.open_file=file
    if not file=='buffer':
        if not os.path.exists('./UserFiles/'+file):
            with open('./UserFiles/'+file,'w') as f:
                pass
        with open('./UserFiles/'+state.open_file,'r') as f:
            state.file_content=f.read()
    else:
        state.file_content=''

#Restarts the whole session to startup state
def restart():
    st.clear()
    state.console=Console(st,startup='./UserFiles/startup.py')
    state.console.synchronize(globals())

#Clears the console's queue
def clear():
    st.clear()

#Declares the python console in which the code will be run.
if 'console' not in state:
    state.console = Console(st,startup='./UserFiles/startup.py')
console=state.console
console.synchronize(globals())


#Run some code in the python console
def process(code,queue):
    if not (code=="" or code==None):
        with queue:
            console.run(code)

#Sets the sidebar menu
def make_menu():
   with stl.sidebar:
        stl.subheader("Menu")
        def on_open_editor_click():
            edit('buffer')
        stl.button("Open Editor",on_click=on_open_editor_click)
        def on_close_editor_click():
            close_editor()
        stl.button("Close Editor",on_click=on_close_editor_click)
        def on_restart_click():
            restart()
        stl.button("Restart Session",on_click=on_restart_click)


#Sets the welcome message header and help expander
def make_welcome():
    stl.subheader("Welcome to StreamPy interactive interpreter.")
    with stl.expander("Click here to get help."):
        with open("Help.md",'r') as f:
            stl.write(f.read())

#Sets the input cell part 
def make_input(queue):
    sti.clear()
    n=len(console.inputs)
    if state.index<=0:
        state.index=0
    elif state.index>n:
        state.index=n

    if n==0 or state.index==0:
        state.input_code.value=""
    else:   
        state.input_code.value=console.inputs[n-state.index]
    
    state.output_code = sti.ace(value=state.input_code.value, placeholder="", language='python', auto_update=True,theme='chrome', min_lines=2, key=state.input_key)
    a,_,b,_,c=sti.columns([1,3,1,3,1],gap='small')
    with a:
        def on_previous_click():
            state.index+=1
            state.input_key=sti.gen_key()
        sti.button("Prev.", key='previous',on_click=on_previous_click)
    with b:
        def on_run_click():
            state.index=0
            process(state.output_code.value,queue)
            state.input_key=sti.gen_key()
        sti.button("Run",key='run_button',on_click=on_run_click)
    with c:  
        def on_next_click():
            state.index-=1
            state.input_key=sti.gen_key()
        sti.button("Next", key='next',on_click=on_next_click)

    sti.refresh()

#Displays the whole console queue
def make_console():
    welcome=stl.container()        
    queue=stl.container()
    state.console_queue=queue
    input=stl.container()

    with welcome:
        make_welcome()   

    with queue:
        st.refresh()

    with input:
        make_input(queue)

#Displays the editor (could be simplified, reorganized, but I somewhat struggled with widget refreshing. This mess is the result of this struggle :) )
def make_editor(editor_column):
    stl.subheader(f"Editing: {os.path.basename(state.open_file)}")
    c1,c2,c3,c4,c5,c6,c7,c8=stl.columns([5,5,5,6,6,5,5,5])
    with c1:
        new_butt=stl.button("New")
    with c2:
        open_butt=stl.button("Open")
    with c3:
        save_butt=stl.button("Save")
    with c4:
        save_as_butt=stl.button("Save as")
    with c5:
        rename_butt=stl.button("Rename")
    with c6:
        delete_butt=stl.button("Delete")
    with c7:
        run_butt=stl.button("Run")
    with c8:
        close_butt=stl.button("Close")
    if close_butt:
        close_editor()
        stl.experimental_rerun()
    elif open_butt:
        def on_file_name_change():
            if not state.file_name==' ':
                edit(state.file_name)
        #stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        basenames = [' ']+[os.path.basename(f) for f in os.listdir('./UserFiles/')]
        stl.selectbox('Select a file:',basenames,on_change=on_file_name_change,index=0,key='file_name')
    elif delete_butt:
        def on_yes():
            os.remove('./UserFiles/'+state.open_file)
            edit('buffer')
            state.editor_key=km.gen_key()
            with editor_column:
                stl.success("File deleted.")
        #stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        stl.selectbox('Are you sure you want to delete this file ?',['No','Yes'],on_change=on_yes,index=0,key='sure')  
    elif new_butt:
        edit('buffer')
        state.editor_key=km.gen_key()
        stl.experimental_rerun()
    else:
        if save_butt:
            if not state.open_file=='buffer':
                save_as(state.open_file)
                stl.success("File saved.")
            else:
                def on_file_name_change():
                    save_as(state.file_name)
                    with editor_column:
                        stl.success("File saved.")
                stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        elif save_as_butt:
            def on_file_name_change():
                save_as(state.file_name)
                with editor_column:
                    stl.success("File saved.")
            stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        elif rename_butt:
            def on_file_name_change():
                os.remove('./UserFiles/'+state.open_file)
                save_as(state.file_name)
                with editor_column:
                    stl.success("File renamed.")
            stl.text_input("Enter new name of file:",on_change=on_file_name_change,key='file_name')
        state.file_content=st_ace(value=state.file_content, placeholder="", language='python', auto_update=True,theme='chrome', min_lines=15, key=state.editor_key)
        if run_butt:
            run_editor_content()
        

#-----------------------------Main app session's logic-------------------------
if state.show_editor==True:
    stl.set_page_config(layout="wide",initial_sidebar_state="collapsed")
    make_menu()
    console_column,editor_column=stl.columns(2)
    with console_column:
        make_console()
    with editor_column:
        make_editor(editor_column)
else:
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    make_menu()
    make_console()






