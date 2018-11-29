package funcs

import (
	//"fmt"
	"github.com/jproxy/g"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"
)

type Platform struct {
	proxyPort   string
	platformUrl string
}

func (this *Platform) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	var access_token string
	cookie, err := r.Cookie("access_token")
	if err == nil {
		access_token = cookie.Value
	}
	remote, err := url.Parse(this.platformUrl)
	if err != nil {
		panic(err)
	}
	timestmap, ok := g.AccessToken()[access_token]
	if ok {
		nowtimestamp := int64(time.Now().Unix())
		if nowtimestamp-timestmap > 600 {
			loginStatus := TestLogin(access_token)
			if loginStatus {
				g.SetAccessToken(access_token)
			} else {
				redirect_url := g.GetLoginUrl()
				http.Redirect(w, r, redirect_url, http.StatusFound)
			}
		}
		httputil.NewSingleHostReverseProxy(remote).ServeHTTP(w, r)
	} else {
		loginStatus := TestLogin(access_token)
		if loginStatus {
			g.SetAccessToken(access_token)
			httputil.NewSingleHostReverseProxy(remote).ServeHTTP(w, r)
		} else {
			redirect_url := g.GetLoginUrl()
			http.Redirect(w, r, redirect_url, http.StatusFound)
		}
	}
}

func StartProxy(proxyPort, platformUrl string) {
	listen_port := ":" + proxyPort
	platform := Platform{platformUrl: platformUrl, proxyPort: proxyPort}
	srv := &http.Server{
		Addr: listen_port, Handler: &platform,
		ReadTimeout: 10 * time.Second, WriteTimeout: 5 * time.Second,
	}

	err := srv.ListenAndServe()
	if err != nil {
		log.Fatalln("ListenAndServe: ", err)
	}
}
