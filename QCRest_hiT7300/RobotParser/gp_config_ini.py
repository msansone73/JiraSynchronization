# Created on 2014-05-12
__author__ = 'Matteo Feroldi'

# Collection of functions to read and write information in config file (.ini file)


from ConfigParser import SafeConfigParser


class ConfigIni():

    def __init__(self, path):

        self.parser = SafeConfigParser()
        self.path = path

    # Read the value from the option inside the session, output: value (string)

    def read_value(self, section, option):
        self.parser.read('%s' % self.path)
        if section in self.parser.sections():
            if option in self.parser.options(section):
                return self.parser.get('%s' % section, '%s' % option)
        else:
            return None


    # Read all values and all options inside the session, output: values list(string), options list(string)

    def read_all_values(self, section):
        self.parser.read('%s' % self.path)
        if section in self.parser.sections():
            options = self.parser.options(section)
            if options:
                values = []
                for value in self.parser.items(section):
                    values.append(value[1])
                return options, values
        else:
            return None


    # Write or change the session information, if the section exist a new session is added

    def write_section(self, section, options, values):
        '''
        Write or change the session information, if the section exist a new session is added
        :param section: Init section
        :param options: Must be a list
        :param values: Must be a list
        :return:
        '''
        self.parser.read('%s' % self.path)
        if section not in self.parser.sections():
            self.parser.add_section('%s' % section)
        for option, value in zip(options, values):
            self.parser.set('%s' % section, '%s' % option, '%s' % value)
        cfgfile = open('%s' % self.path, 'w')
        self.parser.write(cfgfile)
        cfgfile.close()


    # Read all sections, output: sections list(string)

    def read_sections(self):
        self.parser.read('%s' % self.path)
        sections = self.parser.sections()
        return sections

