package g

import (
	"log"
	"os"
	"sync"
	"time"
)

var Root string

func InitRootDir() {
	var err error
	Root, err = os.Getwd()
	if err != nil {
		log.Fatalln("getwd fail:", err)
	}
}

var (
	loginUrl        string
	tokenUrl        string
	accessToken     = make(map[string]int64)
	accessTokenLock = new(sync.RWMutex)
)

func AccessToken() map[string]int64 {
	accessTokenLock.RLock()
	defer accessTokenLock.RUnlock()
	return accessToken
}

func SetAccessToken(token string) {
	accessTokenLock.RLock()
	defer accessTokenLock.RUnlock()
	timestamp := int64(time.Now().Unix())
	accessToken[token] = timestamp
}

func DelAccessToken(token string) {
	accessTokenLock.RLock()
	defer accessTokenLock.RUnlock()
	delete(accessToken,token)
}

func GetLoginUrl() string {
	if Config().Heartbeat.Domain != "" {
		loginUrl = "https://" + Config().Heartbeat.Domain + Config().Heartbeat.LoginUri
	} else {
		loginUrl = "https://" + Config().Outerip + ":" + Config().Heartbeat.Port + Config().Heartbeat.LoginUri
	}
	return loginUrl
}

func GetTokenUrl() string {
	if Config().Heartbeat.Domain != "" {
		tokenUrl = "https://" + Config().Heartbeat.Domain + Config().Heartbeat.TokenUri
	} else {
		tokenUrl = "https://" + Config().Outerip + ":" + Config().Heartbeat.Port + Config().Heartbeat.TokenUri
	}
	return tokenUrl
}
