class LxcReconfigurator:
    def __init__(self, driver):
        self.driver = driver
        self.profile = driver.profile

    def add_mount(self, path, source, readonly=False):
        pass
