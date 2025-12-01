import os
import streamlit as st
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/api")


def get_headers():
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

st.set_page_config(page_title="Analysis & Review", page_icon="Document", layout="wide")

# Check if project_id is in session state
if 'auth_token' not in st.session_state:
    st.warning("You must log in from the home page first.")
    if st.button("Back to Home"):
        st.switch_page("app.py")
    st.stop()

if 'selected_project_id' not in st.session_state:
    st.warning("No project selected. Please go back to the home page and select a document to view.")
    if st.button("Back to Home"):
        st.switch_page("app.py")
    st.stop()

project_id = st.session_state['selected_project_id']

st.title("Analysis & Review")

# Fetch project analysis
try:
    response = requests.get(f"{API_URL}/projects/{project_id}/analysis", headers=get_headers())

    if response.status_code == 200:
        analysis = response.json()

        # Project Metadata
        st.subheader("Project")
        st.markdown(f"### {analysis['name']}")

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.caption("Client Type")
            st.write(analysis.get('client_type') or 'N/A')
            st.caption("Timeline")
            st.write(analysis.get('timeline') or 'N/A')
        with mcol2:
            st.caption("Location")
            st.write(analysis.get('location') or 'N/A')
            st.caption("Budget")
            st.write(analysis.get('budget_range') or 'N/A')

        st.divider()

        # Export Button
        col_export1, col_export2, col_export3 = st.columns([1, 1, 4])
        with col_export1:
            if st.button("Export JSON", use_container_width=True):
                export_response = requests.get(f"{API_URL}/projects/{project_id}/export?format=json", headers=get_headers())
                if export_response.status_code == 200:
                    st.download_button(
                        "Download JSON",
                        data=export_response.text,
                        file_name=f"project_{project_id}_export.json",
                        mime="application/json"
                    )

        with col_export2:
            if st.button("Export CSV", use_container_width=True):
                export_response = requests.get(f"{API_URL}/projects/{project_id}/export?format=csv", headers=get_headers())
                if export_response.status_code == 200:
                    csv_data = export_response.json().get('csv', '')
                    st.download_button(
                        "Download CSV",
                        data=csv_data,
                        file_name=f"project_{project_id}_export.csv",
                        mime="text/csv"
                    )

        st.divider()

        # Spaces and Items (HITL)
        st.header("Spaces & Requirements")

        # Prompt-based additions
        with st.expander("Add via Prompt", expanded=False):
            prompt_text = st.text_area(
                "Describe what to add",
                placeholder="e.g., Add 3 ergonomic chairs to the conference room and a new pantry with a fridge and microwave.",
            )
            if st.button("Generate Additions", type="primary"):
                if not prompt_text.strip():
                    st.warning("Please enter a prompt.")
                else:
                    resp = requests.post(
                        f"{API_URL}/projects/{project_id}/prompt-add",
                        json={"prompt": prompt_text},
                        headers=get_headers(),
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        added_spaces = data.get("created_spaces", [])
                        added_items = data.get("created_items", [])
                        st.success(f"Added {len(added_spaces)} spaces and {len(added_items)} items.")
                        st.rerun()
                    else:
                        st.error(f"Failed to add via prompt: {resp.text}")

        # Add new space form
        with st.expander("Add New Space", expanded=False):
            with st.form("add_space_form"):
                room_type = st.text_input("Room Type", value="")
                dimension = st.text_input("Dimension", value="")
                area = st.text_input("Area", value="")
                with st.expander("Optional: Add an Item with the Space", expanded=False):
                    item_name = st.text_input("Item Name", value="", key="new_space_item_name")
                    item_category = st.text_input("Item Category", value="", key="new_space_item_cat")
                    item_specs = st.text_area("Technical Specs", value="", key="new_space_item_specs")
                    item_qty = st.number_input("Quantity", value=1, min_value=1, key="new_space_item_qty")
                    item_material = st.text_input("Material", value="", key="new_space_item_mat")
                    item_color = st.text_input("Color", value="", key="new_space_item_color")
                    item_brand = st.text_input("Brand", value="", key="new_space_item_brand")
                    item_instruction = st.text_area("Special Instructions", value="", key="new_space_item_instr")
                submit_space = st.form_submit_button("Create Space", type="primary")

            if submit_space:
                space_payload = {
                    "room_type": room_type,
                    "dimension": dimension or None,
                    "area": area or None,
                }
                if item_name or item_category or item_specs or item_material or item_color or item_brand or item_instruction:
                    space_payload["items"] = [{
                        "name": item_name or None,
                        "category": item_category or None,
                        "technical_specs": item_specs or None,
                        "material_preference": item_material or None,
                        "color_preference": item_color or None,
                        "brand_preference": item_brand or None,
                        "special_instruction": item_instruction or None,
                        "quantity": item_qty or None,
                    }]
                resp = requests.post(f"{API_URL}/projects/{project_id}/spaces", json=space_payload, headers=get_headers())
                if resp.status_code == 200:
                    st.success("Space added.")
                    st.rerun()
                else:
                    st.error(f"Failed to add space: {resp.text}")

        if "spaces" in analysis and analysis["spaces"]:
            for space_idx, space in enumerate(analysis["spaces"]):
                with st.expander(f"**{space['room_type']}** - {space.get('dimension', 'N/A')} ({space.get('area', 'N/A')})", expanded=True):

                    if "items" in space and space["items"]:
                        grouped = {}
                        for item in space["items"]:
                            cat = item.get("category") or "Uncategorized"
                            grouped.setdefault(cat, []).append(item)

                        for category, items in grouped.items():
                            with st.expander(f"Category: {category}", expanded=False):
                                for item_idx, item in enumerate(items):
                                    confidence = item.get("confidence")
                                    badge = ""
                                    if confidence is not None:
                                        level = float(confidence)
                                        if level >= 0.75:
                                            color = "#1f7a1f"
                                        elif level >= 0.5:
                                            color = "#b38600"
                                        else:
                                            color = "#a33"
                                        badge = f" <span style='display:inline-block;margin-left:8px;width:14px;height:14px;border-radius:7px;background:{color};'></span>"

                                    st.markdown(f"### {item['name']}{badge}", unsafe_allow_html=True)

                                    form_key = f"item_form_{space_idx}_{category}_{item_idx}_{item['id']}"
                                    with st.form(key=form_key):
                                        col_a, col_b = st.columns(2)

                                        with col_a:
                                            new_name = st.text_input("Item Name", value=item['name'], key=f"name_{item['id']}")
                                            new_category = st.text_input("Category", value=item['category'], key=f"cat_{item['id']}")
                                            new_specs = st.text_area("Technical Specs", value=item.get('technical_specs') or "", key=f"specs_{item['id']}")
                                            new_qty = st.number_input("Quantity", value=item.get('quantity') or 1, min_value=1, key=f"qty_{item['id']}")

                                        with col_b:
                                            new_material = st.text_input("Material", value=item.get('material_preference') or "", key=f"mat_{item['id']}")
                                            new_color = st.text_input("Color", value=item.get('color_preference') or "", key=f"color_{item['id']}")
                                            new_brand = st.text_input("Brand", value=item.get('brand_preference') or "", key=f"brand_{item['id']}")
                                            new_instruction = st.text_area("Special Instructions", value=item.get('special_instruction') or "", key=f"inst_{item['id']}")

                                        # Submit button
                                        col_action1, col_action2, col_action3 = st.columns([1, 1, 1])
                                        with col_action1:
                                            update_clicked = st.form_submit_button("Update Item", type="primary")
                                        with col_action2:
                                            accept_clicked = st.form_submit_button("Accept", type="secondary")
                                        with col_action3:
                                            reject_clicked = st.form_submit_button("Reject", type="secondary")

                                        if update_clicked:
                                            update_data = {
                                                "name": new_name,
                                                "category": new_category,
                                                "technical_specs": new_specs,
                                                "material_preference": new_material,
                                                "color_preference": new_color,
                                                "brand_preference": new_brand,
                                                "special_instruction": new_instruction,
                                                "quantity": new_qty
                                            }

                                            update_response = requests.patch(
                                                f"{API_URL}/projects/{project_id}/requirements/{item['id']}",
                                                json=update_data,
                                                headers=get_headers(),
                                            )

                                            if update_response.status_code == 200:
                                                st.success("Item updated successfully.")
                                                st.rerun()
                                            else:
                                                st.error(f"Update failed: {update_response.text}")

                                        if accept_clicked or reject_clicked:
                                            patch_body = {"is_accepted": True} if accept_clicked else {"is_accepted": False}
                                            resp = requests.patch(
                                                f"{API_URL}/projects/{project_id}/requirements/{item['id']}",
                                                json=patch_body,
                                                headers=get_headers(),
                                            )
                                            if resp.status_code == 200:
                                                st.success("Item status updated.")
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to update status: {resp.text}")

                                        st.divider()
                    else:
                        st.info("No items found for this space.")

                    # Add item to this space
                    with st.expander("Add Item to this Space", expanded=False):
                        with st.form(key=f"add_item_form_{space_idx}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                add_name = st.text_input("Item Name", value="", key=f"add_name_{space['id']}")
                                add_category = st.text_input("Category", value="", key=f"add_cat_{space['id']}")
                                add_specs = st.text_area("Technical Specs", value="", key=f"add_specs_{space['id']}")
                                add_qty = st.number_input("Quantity", value=1, min_value=1, key=f"add_qty_{space['id']}")
                            with col2:
                                add_material = st.text_input("Material", value="", key=f"add_mat_{space['id']}")
                                add_color = st.text_input("Color", value="", key=f"add_color_{space['id']}")
                                add_brand = st.text_input("Brand", value="", key=f"add_brand_{space['id']}")
                                add_instruction = st.text_area("Special Instructions", value="", key=f"add_instr_{space['id']}")
                            if st.form_submit_button("Add Item", type="secondary"):
                                payload = {
                                    "name": add_name or None,
                                    "category": add_category or None,
                                    "technical_specs": add_specs or None,
                                    "material_preference": add_material or None,
                                    "color_preference": add_color or None,
                                    "brand_preference": add_brand or None,
                                    "special_instruction": add_instruction or None,
                                    "quantity": add_qty or None,
                                }
                                add_resp = requests.post(
                                    f"{API_URL}/spaces/{space['id']}/items",
                                    json=payload,
                                    headers=get_headers(),
                                )
                                if add_resp.status_code == 200:
                                    st.success("Item added.")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to add item: {add_resp.text}")
        else:
            st.info("No spaces extracted from the document.")

    else:
        st.error(f"Failed to load analysis: {response.text}")

except Exception as e:
    st.error(f"Error: {str(e)}")

# Back button
st.divider()
if st.button("Back to Documents"):
    st.switch_page("app.py")
