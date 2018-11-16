package funcs

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/jproxy/g"
	"io/ioutil"
	"net/http"
)

func TestLogin(access_token string) bool {
	client := &http.Client{}
	req, err := http.NewRequest("GET", g.GetTokenUrl(), nil)
	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("Authorization", access_token)
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	var loginStatus map[string]interface{}
	json.Unmarshal(body, &loginStatus)
	status := loginStatus["status"].(bool)
	return status
}

func GetAccessToken() {
	userinfo := make(map[string]interface{})
	userinfo["username"] = g.Config().Username
	userinfo["password"] = g.Config().Password
	bytesData, err := json.Marshal(userinfo)
	reader := bytes.NewReader(bytesData)
	client := &http.Client{}
	req, err := http.NewRequest("POST", g.GetTokenUrl(), reader)
	req.Header.Add("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	var info map[string]interface{}
	json.Unmarshal(body, &info)
	if info["status"].(bool) {
		access_token := info["data"].(map[string]interface{})["token"].(string)
		g.SetAccessToken(access_token)
	}
}
