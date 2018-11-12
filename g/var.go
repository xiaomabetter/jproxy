package g

import (
	"log"
	"os"
	"sync"
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
	accessToken     string
	accessTokenLock = new(sync.RWMutex)
)

func AccessToken() string {
	accessTokenLock.RLock()
	defer accessTokenLock.RUnlock()
	return accessToken
}

func SetAccessToken(token string) {
	accessTokenLock.RLock()
	defer accessTokenLock.RUnlock()
	accessToken = token
}
