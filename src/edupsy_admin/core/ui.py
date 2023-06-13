import os
from datetime import date, datetime
import dearpygui.dearpygui as dpg
import edupsy_admin
from appdata import AppDataPaths


def get_app_paths():
    app_paths = AppDataPaths("edupsy_admin")
    print(f"The app data path is: {app_paths.app_data_path}")
    if not os.path.exists(app_paths.app_data_path):
        print("Creating the app data path")
        app_paths.setup()
    return app_paths


def create_connection(sender, app_data, user_data):
    print(f"sender: {sender}")
    print(f"app_data: {app_data}")
    print(f"user_data: {user_data}")
    print(f"dpg.get_value(user_data): {dpg.get_value(user_data)}")
    if sender == "fldlg0":
        print(f"app_data['file_path_name']: {app_data['file_path_name']}")

    app_paths = get_app_paths()
    connection = edupsy_admin.Connection(
        os.path.join(app_paths.app_data_path, dpg.get_value(user_data) + ".sqlite")
    )
    print("Connection created")
    connection.close()
    print("Connection closed")


# today's date (dpg starts counting years at 1900)
TODAY = {
    "month_day": date.today().day,
    "year": date.today().year - 1900,
    "month": date.today().month,
}

###
### Creating the main window
###

dpg.create_context()

with dpg.window(tag="Primary Window"):
    # heading
    dpg.add_text("Select an existing database or create a new one:")

    # option to select an existing database
    dpg.add_listbox(items=["test_db1", "test_db2"], tag="lstbx0", num_items=3)
    dpg.add_button(
        tag="btn0", label="Select", callback=create_connection, user_data="lstbx0"
    )

    # option to create a new database
    dpg.add_input_text(tag="inpttxt0")
    dpg.add_button(
        tag="btn1",
        label="Create",
        callback=lambda: dpg.show_item("fldlg0"),
    )

    # date_picker
    dpg.add_date_picker(default_value=TODAY)

    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=create_connection,
        tag="fldlg0",
        user_data="inpttxt0",
        width=500,
        height=400,
    ):
        dpg.add_file_extension(".csv")

dpg.create_viewport(title="edupsy_admin", width=700, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()
