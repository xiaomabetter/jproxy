package http

import (
	"net/http"
	"github.com/jproxy/g"
)

func configControlRoutes() {
	http.HandleFunc("/add/platform", func(w http.ResponseWriter, r *http.Request) {
		RenderDataJson(w, []interface{}{g.AccessToken()})
	})
}