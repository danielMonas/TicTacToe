# Game board GUI
import wx
import wx.lib.buttons as buttons
from communicator import *
import time
import os


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.init_board()
        self.comm = Communicator()
        self.login()
        self.mark = ""
        self.interaction = True
        self.toggle_interaction()
        Thread(target=self.handle_input, args=()).start()

    def init_board(self):
        """ Initialize the game's GUI """
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.fg_sizer = wx.FlexGridSizer(rows=3, cols=3, vgap=5, hgap=5)
        font = wx.Font(22, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.match_name = wx.StaticText(self, -1, style=wx.ALIGN_CENTER)
        main_sizer.Add(self.match_name, 0, wx.ALL | wx.CENTER, 5)

        self.buttons = []
        for i in range(9):
            button = buttons.GenToggleButton(self, id=i, size=(100, 100))
            button.SetFont(font)
            button.Bind(wx.EVT_BUTTON, self.button_click)
            self.buttons.append(button)

        self.fg_sizer.AddMany(self.buttons)
        main_sizer.Add(self.fg_sizer, 0, wx.ALL | wx.CENTER, 5)
        self.status_prompt = wx.StaticText(self, -1, style=wx.ALIGN_CENTER)
        self.status_prompt.SetLabel("Waiting for opponent")
        main_sizer.Add(self.status_prompt, 0, wx.ALL | wx.CENTER, 5)
        self.SetSizer(main_sizer)

    def login(self):
        """ Prompting the user to enter a username """
        response = ""
        while response != LOGIN_SUCCESS:
            self.name = wx.GetTextFromUser('Enter username:', 'Login')
            response = self.comm.login(self.name)

    def handle_input(self):
        """ Infinite loop receiving and processing the server's messages """
        while True:
            code, data = self.comm.receive()
            if code == MATCH_READY:
                self.set_match(data)
            elif code == TURN:
                self.turn(int(data[:-1]), data[-1])
            elif code == END_GAME:
                self.end_game(data)
            elif code == TIE:
                self.match_name.SetLabel("It's a tie!")
            if code in (END_GAME, TIE, RESET):
                self.reset_board()

    def end_game(self, mark):
        """ Ending the current game and anouncing the winner. """
        players = self.title.split(" VS ", 1)
        winner = players[0] if mark == 'X' else players[1]
        self.match_name.SetLabel("Player {0} wins!!".format(winner))
        self.Refresh()

    def reset_board(self):
        """ Resetting the board to prepare for a new match """
        time.sleep(10)  # Delay for 10 seconds.
        for button in self.buttons:
            button.SetLabel("")
            button.SetValue(False)
            button.SetBackgroundColour(wx.NullColour)
            button.Disable()
        self.interaction = False
        self.match_name.SetLabel("")
        self.mark = ""
        self.status_prompt.SetLabel("Waiting for opponent")

    def toggle_interaction(self):
        """ Change board interaction status """
        for button in self.buttons:
            if button.GetLabel() == "":
                button.Disable() if self.interaction else button.Enable()
        self.interaction = not self.interaction
        self.Refresh()

    def set_match(self, title):
        """ Updating the board's match status """
        self.match_name.SetLabel(title)
        self.title = title
        self.mark = 'X' if title.find(" VS ") > title.find(self.name) else 'O'
        if self.mark == 'X':
            self.toggle_interaction()
        self.status_prompt.SetLabel("")

    def turn(self, id, mark):
        """ handle a player's turn and update the screen """
        self.buttons[id].SetLabel(mark)
        self.buttons[id].Disable()
        self.toggle_interaction()
        self.Refresh()

    def button_click(self, event):
        """ On button toggle, change the label of the button pressed
            and disable the other buttons unless the user changes their mind """
        index = event.GetEventObject().GetId()
        self.turn(index, self.mark)
        self.comm.send(TURN, str(index) + self.mark)


class Frame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Tic-Tac-Toe", size=(700, 600))
        panel = Panel(self)
        self.Bind(wx.EVT_CLOSE, self.on_exit)

    def on_exit(self, event):
        self.Destroy()
        event.Skip()


def main():
    os.system('cls')
    # Starting up GUI
    app = wx.App(False)
    frame = Frame()
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
