package funcs

import (
	//"fmt"
	"github.com/jproxy/g"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
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

	loginStatus := TestLogin(access_token)
	if loginStatus {
		remote, err := url.Parse(this.platformUrl)
		if err != nil {
			panic(err)
		}
		httputil.NewSingleHostReverseProxy(remote).ServeHTTP(w, r)
	} else {
		redirect_url := g.Config().LoginUrl
		http.Redirect(w, r, redirect_url, http.StatusFound)
	}
}

func StartProxy(proxyPort, platformUrl string) {
	listen_port := ":" + proxyPort
	platform := Platform{platformUrl: platformUrl, proxyPort: proxyPort}
	srv := &http.Server{Addr: listen_port, Handler: &platform}

	err := srv.ListenAndServe()
	if err != nil {
		log.Fatalln("ListenAndServe: ", err)
	}
}
