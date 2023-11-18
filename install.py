from configparser import ConfigParser
import os
import sqlite3



class Install:
    """_summary_
    """


    def __init__(self) -> None:
        """_summary_
        """
        pass



    def __load_config(self) -> None:
        """_summary_
        """
        self.__config = ConfigParser()
        self.__config.read('config.ini')



    def __connect_database(self) -> None:
        """_summary_
        """
        db_path = self.__config['APP']['DATABASE_PATH'] + self.__config['APP']['DATABASE_FILE']
        try:
            self.__connection = sqlite3.connect(db_path)
            self.__cursor = self.__connection.cursor()
        except sqlite3.OperationalError:
            print(f'Connection to database:     failed')



    def __overwrite_config(self) -> None:
        """_summary_
        """
        config_file_template = open('./template/template-config.ini','r')
        config_file = open('config.ini', 'w')
        config_file.writelines(config_file_template)
        config_file_template.close()
        config_file.close()
        print(f'Config overwritten')



    def __create_database_file(self) -> None:
        """_summary_
        """
        try:
            if not os.path.exists(self.__config['APP']['DATABASE_PATH']): 
                os.makedirs(self.__config['APP']['DATABASE_PATH'])
        except:
            print(f"creating database path failed")
        path = self.__config['APP']['DATABASE_PATH'] + self.__config['APP']['DATABASE_FILE']
        
        db = open(path, 'w')
        db.close()
        print(f'Database file created')


    
    def __create_tables(self) -> None:
        """_summary_
        """
        #try:
        ddl = open(self.__config['SETUP']['DATABASE_DDL'],'r')
        self.__cursor.executescript(ddl.read())

        ddl.close()
        print(f'Tables created')
        #except:
            #print(f'ERROR: tables not created')

        pass



    def __is_user_input_yes(self, user_input) -> bool:
        """_summary_

        Args:
            user_input (_type_): _description_

        Returns:
            bool: _description_
        """
        if user_input.lower() == 'yes' or user_input.lower() == 'y':
            return True
        return False



    def __close_database(self) -> None:
        """_summary_
        """
        self.__cursor.close()
        self.__connection.close()



    def main(self) -> None:
        """_summary_
        """
        user_input = False


        print(f'New installation? [yes][y]/[no]')
        new_installation = self.__is_user_input_yes(input())
        print()

        # hole installation
        if new_installation:
            print(f'Are you shure? [yes][y]/[no]')
            new_installation = self.__is_user_input_yes(input())
            print()
        if new_installation:
            print(f'New installation is executed')
            print()

        # config file
        if not new_installation:
            print(f'Do you want to overwrite config.ini?')
            user_input = self.__is_user_input_yes(input())
        if user_input or new_installation:
            self.__overwrite_config()
        print()


        if os.path.exists('config.ini'):
            self.__load_config()
        else:
            self.__overwrite_config()
            

        if os.path.exists(self.__config['APP']['DATABASE_PATH'] + self.__config['APP']['DATABASE_PATH'] ):
            self.__connect_database()
        else:
            exit(0)


        # database
        if not new_installation:
            print(f'Do you want to reset the default database if exists? [yes][y]/[no]')
            user_input = self.__is_user_input_yes(input())
        if user_input or new_installation:
            self.__create_database_file()
            self.__create_tables()
        print()


        self.__close_database()





if __name__ == '__main__':
    print('Install configuration')
    Install().main()
    print('Installation finished')
    
    