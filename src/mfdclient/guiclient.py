import logging
import signal
import sys

import psutil

import PySimpleGUI as PySG

from mfdclient.client import Client

class GuiClient(Client):
    """A simple MFD panel used to interactively test the companion without starting the game in VR"""
    def __init__(self):
        super().__init__(self.data_loaded, self.data_changed)
        self.window = None
        self.gui_tabs = []
        self.active_tab = None
        self.continue_running = True

        signal.signal(signal.SIGINT, self.handle_interrupt)


    def build_tab_layout(self):
        headings = ['Id', 'Label', 'Sublabel', 'Value']

        for tab_id in self.screen_reader.tab_data.keys():
            data = self.screen_reader.tab_data[tab_id]
            self.gui_tabs.append(PySG.Tab(tab_id, [
                [PySG.Table(values=data, headings=headings, auto_size_columns=False, col_widths=[40, 40, 40, 20],
                          expand_x=True, expand_y=True, cols_justification=['l', 'l', 'l', 'r'],
                          key=f"-{tab_id}-table-",
                          visible_column_map=[False, True, True, True],
                          enable_events=True, select_mode=PySG.TABLE_SELECT_MODE_BROWSE)]
            ], key=f"-{tab_id}-tab-"))
        self.active_tab = list(self.screen_reader.tab_data.keys())[0]


    def data_loaded(self):
        self.build_tab_layout()
        tab_group_layout = [
            self.gui_tabs
        ]

        window_title = self.screen_reader.title

        if self.screen_reader.subtitle:
            window_title += f"/{self.screen_reader.subtitle}"

        self.window = PySG.Window(window_title, [
            [PySG.Text(text="Status: "), PySG.Text(text=self.screen_reader.status, key="status")],
            [PySG.TabGroup(tab_group_layout, enable_events=True, key="-TABGROUP-")],
            [PySG.Push(), PySG.Button('Back'), PySG.Button('Select')],
            [PySG.StatusBar(text=self.screen_reader.footer_hint, key="footerHint", size=(100, 1))],
        ], finalize=True, print_event_values=True)

        self.active_tab = list(self.screen_reader.tab_data.keys())[0]
        for tab_id in self.screen_reader.tab_data.keys():
            self.window[f"-{tab_id}-table-"].bind("<Double-Button-1>", " Double")
            self.window[f"-{tab_id}-table-"].bind("<Return>", " Return")
        self.switch_tab("Places")


    def data_changed(self):
        self.window.write_event_value('-update-data-', '')


    def read_screen(self):
        for tab_id in self.screen_reader.tab_data.keys():
            default_selection = self.screen_reader.tab_selections[tab_id]
            selection_list = []

            if tab_id == self.active_tab and default_selection is not None:
                selection_list.append(default_selection)
                logging.debug(f"Setting default selection to {default_selection} for {tab_id}")
            self.window[f"-{tab_id}-table-"].update(values=self.screen_reader.tab_data[tab_id],
                                                    select_rows=selection_list)
            logging.debug("After table update")

        self.window['status'].update(value=self.screen_reader.status)
        self.window['footerHint'].update(value=self.screen_reader.footer_hint or "")

        window_title = self.screen_reader.title

        if self.screen_reader.subtitle:
            window_title += f"/{self.screen_reader.subtitle}"
        self.window.TKroot.title(window_title)


    def run(self):
        self.start()
        while self.continue_running:
            event, values = self.window.read(timeout=100)

            if event == PySG.WIN_CLOSED:
                self.screen_reader.stop()
                sys.exit(0)
            elif event == '-update-data-':
                self.read_screen()
            elif event == 'Select':
                table_key = values['-TABGROUP-'].replace("-tab-", "-table-")
                selection = values[table_key]
                if len(selection) > 0:
                    index = selection[0]
                    self.select_item(index)
            elif event == 'Back':
                table_key = values['-TABGROUP-'].replace("-tab-", "-table-")
                selection = values[table_key]
                if len(selection) > 0:
                    index = selection[0]
                    self.back(index)
                else:
                    self.back(None)
                logging.debug("After back")
            elif event == '-TABGROUP-':
                tab_id = values['-TABGROUP-'][1:-5]
                self.switch_tab(tab_id)
                self.active_tab = tab_id
                logging.info(values["-TABGROUP-"])
            elif event in self.screen_reader.tab_data.keys():
                # Double click or enter key
                table_key = values['-TABGROUP-'].replace("-tab-", "-table-")
                tab_id = event
                selection = values[table_key]
                logging.debug(f"Single click: {tab_id} {selection}")
                if len(selection) > 0:
                    index = selection[0]
                    logging.debug("Before select_item")
                    self.select_item(index)
                logging.debug("After default else")
            elif len(event) == 3 and event[1] == "+CLICKED+":
                tab = event[0]
                #event_type = event[1]
                coordinate = event[2]
                logging.debug(f"Single click: {tab} {coordinate}")
                pass
            elif event.endswith(' Double') or event.endswith(' Return'):
                base_event = event.replace(' Double', '').replace(' Return', '')
                tab = base_event.replace('-table-', '').replace("-", "")
                table_key = values['-TABGROUP-'].replace("-tab-", "-table-")
                if values[table_key]:
                    row_index = values[table_key][0]
                    logging.debug(f"Double click {tab} row index: {row_index}")
                    self.select_item(row_index)
                else:
                    logging.debug("Double click event with no selected item")
            elif event.endswith('-table-'):
                tab_id = values['-TABGROUP-'][1:-5]
                table_key = values['-TABGROUP-'].replace("-tab-", "-table-")
                table_data = values[table_key]
                if table_data:
                    row_index = table_data[0]
                    if row_index < self.get_item_count(tab_id):
                        self.nav_item(row_index)
                else:
                    logging.debug("No data for table")


        self.window.close()


    @staticmethod
    def exit_if_game_running():
        # If this client appends an event with a high number, the panel in the game will stop responding to events
        # until the event sequence catches up to what was set here.
        for process in psutil.process_iter():
            name = process.name()
            if name == "EliteDangerous64" or name == "EliteDangerous64.exe":
                logging.error("The game is running - exiting to avoid corrupting the event file")
                # sys.exit(0)


    def select_item(self, index):
        self.exit_if_game_running()
        super().select_item(index)


    def nav_item(self, index):
        self.exit_if_game_running()
        super().nav_item(index)


    def back(self, index):
        self.exit_if_game_running()
        super().back(index)


    def switch_tab(self, tab_id):
        self.exit_if_game_running()
        super().switch_tab(tab_id)


    def handle_interrupt(self, _signum, _frame):
        logging.debug("Shutting down on signal")
        self.continue_running = False
        self.stop()
        sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    gui = GuiClient()
    gui.run()
