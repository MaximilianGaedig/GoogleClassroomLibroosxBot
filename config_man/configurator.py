from pathlib import Path
import shutil

import yaml


class ConfingMan:
    def __init__(self, filename='config.yml'):
        self.__p = Path(filename)
        if not self.__p.exists():
            sample_config = Path('config_man/sampleconfig.yml')
            shutil.copyfile(sample_config, self.__p)
            raise Exception(f'Missing {self.__p}, created sample')

        with open(self.__p, 'r') as file:
            self.conf_dict = yaml.safe_load(file)

    def save(self):
        with open(self.__p, 'w') as file:
            yaml.dump(self.conf_dict, file)

    @property
    def google_credentials(self):
        if self.conf_dict.get('google') is not None:
            if self.conf_dict.get('google').get('email') is None or self.conf_dict.get('google').get('passwd') is None:
                raise Exception('Nie ma danych do logowania do google!')
        else:
            raise Exception('Nie ma kategorii google w pliku konfiguracyjnym!')
        return self.conf_dict.get('google').get('email'), self.conf_dict.get('google').get('passwd')

    @property
    def librus_credentials(self):
        if self.conf_dict.get('librus') is not None:
            if self.conf_dict.get('librus').get('email') is None or self.conf_dict.get('librus').get('passwd') is None:
                raise Exception('Nie ma danych do logowania do google!')
        else:
            raise Exception('Nie ma kategorii librus w pliku konfiguracyjnym!')
        return self.conf_dict.get('librus').get('email'), self.conf_dict.get('librus').get('passwd')

    @property
    def chrome_args(self):
        a = self.conf_dict.get('chrome').get('args')
        if a is None:
            a = []
        return a

    @property
    def chrome_exp(self):
        e = self.conf_dict.get('chrome').get('experimental')
        if e is None:
            e = []
        return e
