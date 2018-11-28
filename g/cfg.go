package g

import (
	"encoding/json"
	"github.com/toolkits/file"
	"log"
	"sync"
	"os"
)

type HeartbeatConfig struct {
	Username    string `json:"username"`
	Password    string `json:"password"`
	Host        string `json:"host"`
	Port        string `json:"port"`
	TokenUri    string `json:"verify_token_uri"`
	LoginUri    string `json:"login_url"`
	PlatformUri string `json:"platform_info_uri"`
}

type GlobalConfig struct {
	Debug     bool             `json:"debug"`
	Location  string           `json:"location"`
	Domain    string           `json:"domain"`
	Outerip   string           `json:"outerip"`
	Heartbeat *HeartbeatConfig `json:"heartbeat"`
}

var (
	ConfigFile string
	config     *GlobalConfig
	lock       = new(sync.RWMutex)
)

func Config() *GlobalConfig {
	lock.RLock()
	defer lock.RUnlock()
	return config
}

func ParseConfig(cfg string) {
	if cfg == "" {
		log.Fatalln("use -c to specify configuration file")
	}

	if !file.IsExist(cfg) {
		log.Fatalln("config file:", cfg, "is not existent. maybe you need `mv cfg.example.json cfg.json`")
	}

	ConfigFile = cfg

	configContent, err := file.ToTrimString(cfg)
	if err != nil {
		log.Fatalln("read config file:", cfg, "fail:", err)
	}

	var c GlobalConfig
	err = json.Unmarshal([]byte(configContent), &c)
	if err != nil {
		log.Fatalln("parse config file:", cfg, "fail:", err)
	}

	lock.Lock()
	defer lock.Unlock()

	if c.Domain == "" || c.Outerip == "" || c.Location == "" {
		log.Fatalln("parse config file:", cfg, "fail:", "domain or outerip or location must be set")
		os.Exit(1)
	}

	if c.Heartbeat.Host == "" || c.Heartbeat.Username == "" || c.Heartbeat.Password == "" || c.Heartbeat.Port == ""  {
		log.Fatalln("parse config file:", cfg, "fail:", "Host Username Password Port must be set")
		os.Exit(1)
	}

	if c.Heartbeat.LoginUri == "" || c.Heartbeat.TokenUri == ""  {
		log.Fatalln("parse config file:", cfg, "fail:", "LoginUri TokenUri must be set")
		os.Exit(1)
	}

	config = &c

	log.Println("read config file:", cfg, "successfully")
}
