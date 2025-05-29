class Theme:
    def __init__(self):
        self.__windowBg = (30, 30, 30)
        self.__buttonBg = (50, 50, 50)
        self.__activeButtonBg = (95, 95, 95)
        self.__closeButtonBg = (200,30,30)
        self.__closeActiveButtonBg = (100,50,50)


    def windowBg(self):
        return self.get_rgb(self.__windowBg)

    def buttonBg(self):
        return self.get_rgb(self.__buttonBg)

    def activeButtonBg(self):
        return self.get_rgb(self.__activeButtonBg)

    def closeButtonBg(self):
        return self.get_rgb(self.__closeButtonBg)

    def closeActiveButtonBg(self):
        return self.get_rgb(self.__closeActiveButtonBg)

    def get_rgb(self, rgb):
        return "#%02x%02x%02x" % rgb

if __name__ == "__main__":
    theme = Theme()
    print(theme.windowBg())