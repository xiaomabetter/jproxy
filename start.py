import sys,time,os,atexit,signal,logging,json
import subprocess
import requests
import argparse

log = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

class Daemon:
    startmsg = "server started with pid %s"

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        log.info("create daemon pidfile at:%s" % self.pidfile)

    def daemonize(self):
        signal.signal(signal.SIGCHLD,signal.SIG_IGN)
        try:
            pid = os.fork()
            if pid > 0:
                log.info("1. fork 1# ----  ppid:%s" % str(os.getpid()))
                sys.exit(0)
        except OSError as e:
            log.error("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        log.info("2. fork 1# ----   pid:%s" % str(os.getpid()))
        os.chdir("/")
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                log.info("3. fork 2# ----   ppid:%s" % str(os.getpid()))
                os._exit(0)
        except OSError as e:
            log.error("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        log.info("4. fork 2# ----   pid:%s" % str(os.getpid()))
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        atexit.register(self.delpid)
        pid = str(os.getpid())
        log.info("write pid : %s to pidfile : %s" %(pid, self.pidfile))
        open(self.pidfile, 'w+').write("%s\n" % pid)


    def delpid(self):
        os.remove(self.pidfile)
        log.info("do pid : %s os remove(%s)" % (str(os.getpid()), self.pidfile))

    def start(self):
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            log.warning(message % self.pidfile)
            sys.exit(1)

        self.daemonize()
        self.run()

    def stop(self):
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                    log.info("pid : %s delete pidfile : %s" % (str(os.getpid()), self.pidfile))
            else:
                print(str(err))
                sys.exit(1)
        os.popen("ps aux|grep jproxy|awk '{print $2}'|xargs kill -9").read()

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        pass


class startDaemon(Daemon):
    def __init__(self, save_path, stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
        Daemon.__init__(self, save_path, stdin, stdout, stderr,)
        self.initconfig()
        self.token = None

    def initconfig(self):
        with open('cfg.json') as f:
            globalConfig = json.loads(f.read())
            self.globalConfig = globalConfig
            verify_token_uri = globalConfig['heartbeat']['verify_token_uri']
            platform_info_uri = globalConfig['heartbeat']['platform_info_uri']
            update_node_uri = globalConfig['heartbeat']['update_node_uri']
            if globalConfig['heartbeat']['domain'] != '' :
                platform_host = globalConfig['heartbeat']['domain']
                self.get_token_url = "https://{0}{1}".format(platform_host, verify_token_uri)
                self.verif_token_url = "https://{0}{1}".format(platform_host,verify_token_uri)
                self.platform_info_url = "https://{0}{1}".format(platform_host,platform_info_uri)
                self.update_node_uri = "https://{0}{1}".format(platform_host,update_node_uri)
            else:
                platform_host = globalConfig['heartbeat']['host']
                platform_port = globalConfig['heartbeat']['port']
                self.get_token_url = "https://{0}:{1}{2}".format(platform_host, platform_port, verify_token_uri)
                self.verif_token_url = "https://{0}:{1}{2}".format(platform_host, platform_port,verify_token_uri)
                self.platform_info_url = "https://{0}:{1}{2}".format(platform_host, platform_port,platform_info_uri)
                self.update_node_uri = "https://{0}:{1}{2}".format(platform_host, platform_port,update_node_uri)
            self.username = globalConfig['heartbeat']['username']
            self.password = globalConfig['heartbeat']['password']
            self.location = globalConfig['location']
        f.close()

    def getToken(self):
        headers = {'Content-Type': 'application/json'}
        data = {"username": self.username, "password": self.password}
        r = requests.post(self.get_token_url, headers=headers, data=json.dumps(data))
        token = r.json()['data']['token']
        self.token = token

    def verifyToken(self):
        headers = {'Content-Type': 'application/json'}
        headers['Authorization'] = self.token
        r = requests.get(self.get_token_url, headers=headers)
        data = r.json()
        return data['status']

    def getAllProxy(self):
        if not self.token:
            self.getToken()
        headers = {'Content-Type': 'application/json'}
        headers['Authorization'] = self.token
        try:
            r = requests.get(self.platform_info_url, headers=headers)
            platforms = r.json()['data']
            return platforms
        except Exception as e:
            return []

    def startProxy(self,proxyport, platform_url):
        success = False
        count = 1
        while not success and count <= 3:
            cmd = [
                "./jproxy",
                '-proxyport', str(proxyport),
                '-proxyurl', platform_url,
            ]
            p = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=sys.stderr, cwd=BASE_DIR)
            if p.errors is None:
                return True
            else:
                success = False
                count = count + 1
        return False

    def stopProxy(self,proxyport):
        os.environ.setdefault('PYTHONOPTIMIZE', '1')
        if os.getuid() == 0:
            os.environ.setdefault('C_FORCE_ROOT', '1')
        success = False
        count = 1
        while not success and count <= 3:
            cmd = "ps aux|grep jproxy|awk '{if($13 == \"%s\")print $2}'|xargs kill" % proxyport
            p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE, stderr=sys.stderr)
            if p.errors is None:
                return True
            else:
                success = False
                count = count + 1
        return False

    def updateProxyNode(self) :
        if not self.token:
            self.getToken()
        headers = {'Content-Type': 'application/json'}
        headers['Authorization'] = self.token
        try:
            node = {'location':self.globalConfig['location'],'outerip':self.globalConfig['outerip'],
                    'domain':self.globalConfig['domain']}
            r = requests.post(self.update_node_uri, headers=headers,data=json.dumps(node))
            data = r.json()
            return data['status']
        except Exception as e:
            return False

    def run(self):
        while True :
            current_platform_list = []
            new_platform_list = []
            platforms = self.getAllProxy()
            self.updateProxyNode()
            for index,platform in enumerate(platforms):
                if platform['location'] == self.location and platform['isproxy']:
                    platform_url = platform['platform_url']
                    proxyport = platform['proxyport']
                    new_platform_list.append(proxyport)
                    cmd = "ps aux|grep jproxy|awk '{if($13 == \"%s\")print}'" % proxyport
                    r = os.popen(cmd).read()
                    if r:
                        if platform_url != r.strip().split()[14]:
                            r = self.stopProxy(proxyport)
                            if r:
                                time.sleep(3)
                                self.startProxy(proxyport, platform_url)
                    else:
                        self.startProxy(proxyport, platform_url)
            cmd = "ps aux|grep jproxy|grep -v 'grep'| awk '{print $13}'"
            p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE, stderr=sys.stderr)
            for line in p.stdout.readlines():
                current_platform_list.append(line.decode().strip("\n"))
            for port in current_platform_list:
                if port not in new_platform_list:
                    self.stopProxy(port)
            time.sleep(30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""
        Easemob Ops service control tools;
        Example: \r\n
        %(prog)s start ;
        """
    )
    parser.add_argument(
        'action', type=str,
        choices=("start", "stop", "restart", "status"),
        help="Action to run"
    )
    args = parser.parse_args()

    pid_fn = '/tmp/daemon_class.pid'
    err_fn = '/tmp/daemon_class.err'

    sd = startDaemon(pid_fn,stderr=err_fn)

    action = args.action

    if action == "start":
        sd.start()
    elif action == "stop":
        sd.stop()
    elif action == "restart":
        sd.stop()
        sd.start()