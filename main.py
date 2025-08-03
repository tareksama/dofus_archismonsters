import streamlit as st
import pandas as pd
import math
import base64

from database import Database

from login import require_login  # <-- add this

require_login() 

def path_to_img_html(path):
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
    except:
        return f'<h4>None</h4>'
    return f'data:image/png;base64,{data}'

# Load data
db = Database()
user_name = st.session_state.username
user = db.get_user_by_name(user_name)
monsters = db.get_user_monsters(user_name)
steps = {m.step for m in monsters}
zones = {m.zone for m in monsters}
zone_choice = None
step_choice = None
df = None

with st.sidebar:

    st.subheader(f'Username : {user_name}',divider=True)
    form = st.form("my_form",border=False)
    # Filter input
    search_name = form.text_input("Filter by name")
    owernership_choice = form.selectbox("Filter by ownership", ["All", "Owned", "Not owned"])
    step_choice = form.selectbox("Filter by step", ["All"]+sorted(list(steps)))
    zone_choice = form.selectbox("Filter by zone", ["All"]+sorted(list(zones)))
        
        
    submitted = form.form_submit_button("Filter",use_container_width=True,type="primary")


    if form.submitted:
        if step_choice == "All":
            selected_steps = [int(e) for e in list(steps)]
        else:
            selected_steps = [int(step_choice)]

        if zone_choice == "All":
            selected_zones = list(zones)
        else:
            selected_zones = [zone_choice]

        if owernership_choice == "All" :
            data = []
            filtred_monsters = [m for m in monsters if m.step in selected_steps and m.zone in selected_zones]
            for m in filtred_monsters:
                try:
                    image_name = m.name.replace(" ", "_").replace("/", "_")
                    image_name = f"static/images/{image_name}.png"
                    data.append({"Id": m.id, "Image": image_name, "Name": m.name, "Step": m.step, "Level" : m.level, "Zone": m.zone, "Quantity": m.quantity, "Selection": False})
                except ValueError:
                    continue

            df = pd.DataFrame(data)
            if(len(df)):
                df["Image"] = df["Image"].apply(path_to_img_html)

        if owernership_choice == "Owned":
            filtred_monsters = [m for m in monsters if m.step in selected_steps and m.zone in selected_zones and m.quantity != 0 ]
            data = []
            for m in filtred_monsters:
                try:
                    image_name = m.name.replace(" ", "_").replace("/", "_")
                    image_name = f"static/images/{image_name}.png"
                    data.append({"Id": m.id, "Image": image_name, "Name": m.name, "Step": m.step, "Level" : m.level, "Zone": m.zone, "Quantity": m.quantity, "Selection": False})
                except ValueError:
                    continue

            df = pd.DataFrame(data)

            if(len(df)):
                df["Image"] = df["Image"].apply(path_to_img_html)

        if owernership_choice == "Not owned":
            filtred_monsters = [m for m in monsters if m.step in selected_steps and m.zone in selected_zones and m.quantity == 0 ]
            data = []
            for m in filtred_monsters:
                try:
                    image_name = m.name.replace(" ", "_").replace("/", "_")
                    image_name = f"static/images/{image_name}.png"
                    data.append({"Id": m.id, "Image": image_name, "Name": m.name, "Step": m.step, "Level" : m.level, "Zone": m.zone, "Quantity": m.quantity, "Selection": False})
                except ValueError:
                    continue
            
            df = pd.DataFrame(data)
            if(len(df)):
                df["Image"] = df["Image"].apply(path_to_img_html)

        if(len(df)):
            df = df[df["Name"].str.contains(search_name, case=False, na=False)]
        st.session_state.df = df


df = st.session_state.get("df")

if df is not None and len(df):
    # Initialize selection state
    if "selection_map" not in st.session_state:
        st.session_state.selection_map = {row["Id"]: False for _, row in df.iterrows()}

    # Pagination controls
    col1, col2 = st.columns(2)
    with col1:
        page_size = st.number_input("Size", min_value=4, max_value=20, step=4)
    with col2:
        total_pages = max(1, math.ceil(len(df) / page_size))
        page = st.number_input("Page", min_value=1, max_value=total_pages, step=1)

    start = (page - 1) * page_size
    end = start + page_size
    df_page = df.iloc[start:end].copy()

    
    # Add Select All / Deselect All buttons
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Select All (All Pages)",icon=":material/check:",use_container_width=True):
            for id_ in df["Id"]:
                st.session_state.selection_map[id_] = True
    with c2:
        if st.button("Deselect All (All Pages)",icon=":material/close:",use_container_width=True):
            for id_ in df["Id"]:
                st.session_state.selection_map[id_] = False
    # Add selection state to df before pagination
    df_page["Selection"] = df_page["Id"].map(lambda x: st.session_state.selection_map.get(x, False))
    edited_df = st.data_editor(
        df_page,
        column_config={
            "Id": st.column_config.NumberColumn("Id", help="Id of the monster", disabled=True),
            "Image": st.column_config.ImageColumn("Image", help="Image of the monster"),
            "Level": st.column_config.TextColumn("Level", help="Level of the monster", disabled=True),
            "Step": st.column_config.TextColumn("Step", help="Step of the monster", disabled=True),
            "Zone": st.column_config.TextColumn("Zone", help="Zone of the monster", disabled=True),
            "Quantity": st.column_config.NumberColumn("Quantity", help="Quantity of the monster", disabled=True),
            "Selection": st.column_config.CheckboxColumn("Selection", help="Select to modify quantity", default=False),
        },
        hide_index=True
    )

    # Update session state based on edits
    for _, row in edited_df.iterrows():
        st.session_state.selection_map[row["Id"]] = row["Selection"]

    # Get selected IDs from global state
    monster_ids = [k for k, v in st.session_state.selection_map.items() if v]

    if monster_ids:
        c1, c2 = st.columns([1, 1])
        with c1:
            add = st.button("Increase", help="Increase monster's quantity", icon=":material/add:", use_container_width=True)
        with c2:
            subs = st.button("Decrease", help="Decrease monster's quantity", icon=":material/remove:", use_container_width=True)

        if add:
            db.update_user_monster_quantity(user.id, monster_ids, 1)
            st.rerun()
        if subs:
            db.update_user_monster_quantity(user.id, monster_ids, -1)
            st.rerun()

else:
    st.warning('Monsters not found', icon="⚠️")
