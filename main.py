import argparse
import json
import os
import socket
from time import sleep, ctime
from typing import cast
import warnings

from ubiquiti.unifi import API, LoggedInException

# Filtering out ssl warnings
warnings.filterwarnings("ignore")


class DockerEnviron(dict):
    def __getitem__(self, key):
        if (key_file := os.environ.get(f"{key}__FILE", "")):
            if os.path.exists(key_file):
                with open(key_file, 'r') as fd:
                    return fd.read()
        elif key in os.environ.keys():
            return os.environ.get(key)
        raise KeyError()

    def get(self, key, default=None):
        'D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.'
        try:
            return self[key]
        except KeyError:
            return default

    def get_bool(self, key, default=None):
        """Attempt to convert a string in an environment to a boolean. 
        Case insensitive: true, 1, t, y, yes
        """
        if (val := self.get(key, default)) is not None:
            return str(val).lower() in ['true', '1', 't', 'y', 'yes']
        return None

    def get_int(self, key, default=None):
        """Attempt to convert a string in an environment to an integer."""
        if (val := self.get(key, default)) is not None:
            return int(cast(str, val))
        return None


class MoreAPI(API):
    def get_client_data(self, mac: str) -> dict:
        r = self._session.get(f"{self._baseurl}/api/s/{self._site}/stat/user/{mac}", verify=self._verify_ssl)

        if self._current_status_code == 401:
            raise LoggedInException("Invalid login, or login has expired")

        resp_data = r.json()
        return resp_data

    def update_alias(self, client_id: str, alias: str) -> bool:
        """
        Update the alias for a client
        :param client_id: the client guid to update (obtain from list_clients)
        :param alias: the new alias to assign
        :return: success
        """
        json_data = json.dumps({'name': alias})
        r = self._session.put(f"{self._baseurl}/api/s/{self._site}/rest/user/{client_id}",
                               data=json_data,
                               verify=self._verify_ssl)
        self._current_status_code = r.status_code
        
        if self._current_status_code == 401:
            raise LoggedInException("Invalid login, or login has expired")

        resp_data = r.json()
        return resp_data['meta']['rc'] == "ok"


def get_hostname_from_ip(ip: str):
    try:
        return socket.gethostbyaddr(ip)
    except:
        return None


def update_all_clients(username: str,
                       password: str,
                       site: str,
                       baseurl: str,
                       verify_ssl: bool) -> int:
    """Update all Unifi clients' alias with their current hostname as recorded in DNS"""
    log_print("{} - Updating all clients".format(ctime()))
    with MoreAPI(username=username, password=password, site=site, baseurl=baseurl, verify_ssl=verify_ssl) as api:
        update_count = 0
        clients = api.list_clients()
        for client in clients:
            if (client_id:= client.get('user_id')) is not None:
                ip = client.get('ip')
                new_name = get_hostname_from_ip(ip)
                if new_name is None:
                    continue
                #new_name = '.'.join(new_name[0].split('.')[:-1])
                new_name = new_name[0].split('.', 1)[0]
                cur_name = client.get('name')
                if not cur_name == new_name:
                    res = api.update_alias(client_id, new_name)
                    if res:
                        update_count += 1
                        log_print(f"{ip}: {cur_name} -> {new_name}")
                    else:
                        log_print(f"Unable to update {ip}!")
    return update_count


def type_environ_var(val):
    if val is None:
        raise argparse.ArgumentTypeError('is missing. Pass in as an argument, or set an environment var of the same name. Use <name>__FILE to read the value from a file (useful for docker secrets).')
    return val


def log_print(message):
    print("{} - {}".format(ctime(), message))


if __name__ == "__main__":
    de = DockerEnviron()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Update all Unifi clients' alias with their current\
                     hostname as recorded in DNS.\n\nNote: All arguments\
                     may be passed in by environment variable of the same long name.\
                     Append __FILE to read the value from a file.")
    # Mandatory
    parser.add_argument('-u', '--username', dest="username", type=type_environ_var, default=de.get('USERNAME'))
    parser.add_argument('-p', '--password', dest="password", type=type_environ_var, default=de.get('PASSWORD'))
    # Optional
    parser.add_argument('--site', 
                        dest="site",
                        type=type_environ_var,
                        default=de.get('SITE', 'default'),
                        help="The name/id of the site to use")
    parser.add_argument('--base-url',
                        dest="base_url",
                        type=type_environ_var,
                        default=de.get('BASE_URL', 'https://unifi:8443'),
                        help="The base url to use to access the unifi controller")
    parser.add_argument('--no-verify-ssl',
                        dest="verify_ssl",
                        action="store_false",
                        default=de.get_bool('VERIFY_SSL', True),
                        help="Do not verify SSL")
    parser.add_argument('--daemonize',
                        dest="daemonize",
                        metavar="SECONDS",
                        default=de.get_int('DAEMONIZE', 0),
                        help="Daemonize, and run every N seconds")
    args = parser.parse_args()
    args.base_url = args.base_url.rstrip('/')
    log_print("Starting Up")
    if not args.daemonize:
        # Go ahead and run once
        update_all_clients(args.username, args.password, args.site, args.base_url, args.verify_ssl)
    while args.daemonize > 0:
        # Otherwise start a loop executing every args.daemonize seconds
        update_all_clients(args.username, args.password, args.site, args.base_url, args.verify_ssl)
        sleep(args.daemonize)
    log_print("Shutting Down")
